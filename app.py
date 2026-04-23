import os
import secrets
from pathlib import Path
from datetime import datetime
import base64
import hashlib
import hmac
import json

from flask import Flask, request, send_file, render_template_string, flash, redirect, after_this_request, session
from werkzeug.utils import secure_filename

from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

from config import Config
from config import SP_SITE_URL, SP_DOC_LIBRARY, SP_CLIENT_ID, SP_CLIENT_SECRET
from src.process import format_raw_file
from src.sred_utils import safe_upload_file

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-local-only-change-me")

GEOHUB_URL = os.environ.get("GEOHUB_URL", "").rstrip("/")
GEOHUB_SSO_SHARED_SECRET = os.environ.get("GEOHUB_SSO_SHARED_SECRET", "")
NEXT_PUBLIC_DATALOGGER_URL = os.environ.get("NEXT_PUBLIC_DATALOGGER_URL", "").rstrip("/")
AUTH_METHOD = os.environ.get("AUTH_METHOD", "").strip().lower()

PROJECT_ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = PROJECT_ROOT / "tmp_test_raw"
FORMATTED_DIR = PROJECT_ROOT / "tmp_test_formatted"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FORMATTED_DIR.mkdir(parents=True, exist_ok=True)

# Override formatted output path for this standalone local app.
Config.FORMATTED_DIR = str(FORMATTED_DIR)


def _redirect_target() -> str:
    return NEXT_PUBLIC_DATALOGGER_URL or GEOHUB_URL or "/"


def _is_local_request() -> bool:
    remote = (request.remote_addr or "").strip()
    forwarded_for = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    candidate = forwarded_for or remote
    return candidate in {"127.0.0.1", "::1", "localhost"}


def _b64url_decode(input_str: str) -> bytes:
    s = input_str.replace("-", "+").replace("_", "/")
    padding = "=" * ((4 - (len(s) % 4)) % 4)
    return base64.b64decode(s + padding)


def _verify_geohub_sso_token(token: str) -> dict:
    """
    Token format: <base64url(payload-json)>.<base64url(hmac_sha256(payloadB64, secret))>
    Shared secret: GEOHUB_SSO_SHARED_SECRET
    """
    if not GEOHUB_SSO_SHARED_SECRET:
        raise ValueError("GEOHUB_SSO_SHARED_SECRET is not configured")

    try:
        payload_b64, sig_b64 = token.split(".", 1)
    except ValueError:
        raise ValueError("Invalid token format")

    expected_sig = hmac.new(
        GEOHUB_SSO_SHARED_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    actual_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")

    payload_raw = _b64url_decode(payload_b64).decode("utf-8")
    payload = json.loads(payload_raw)

    now = int(datetime.utcnow().timestamp())
    exp = int(payload.get("exp", 0) or 0)
    if exp and now > exp:
        raise ValueError("Token expired")

    aud_expected = os.getenv("DATALOGGER_SSO_AUDIENCE", "datalogger")
    if payload.get("aud") and payload.get("aud") != aud_expected:
        raise ValueError("Invalid token audience")

    iss_expected = os.getenv("DATALOGGER_SSO_ISSUER", "geohub")
    if payload.get("iss") and payload.get("iss") != iss_expected:
        raise ValueError("Invalid token issuer")

    if not payload.get("sub"):
        raise ValueError("Token missing subject")

    return payload


def _geohub_sso_start_url(next_path: str) -> str | None:
    explicit = os.getenv("GEOHUB_DATALOGGER_SSO_START_URL", "").strip()
    if explicit:
        return f"{explicit}?next={next_path}"
    if GEOHUB_URL:
        return f"{GEOHUB_URL}/api/sso/datalogger?next={next_path}"
    return None


@app.before_request
def _enforce_auth():
    if request.path.startswith("/static/"):
        return None
    if request.path in {"/auth/sso/callback", "/auth/logout", "/healthz"}:
        return None

    # Non-geohub mode is local-only.
    if AUTH_METHOD != "geohub":
        if _is_local_request():
            return None
        return "Local mode only. Use http://127.0.0.1", 403

    if session.get("user"):
        return None

    next_path = request.full_path if request.query_string else request.path
    start = _geohub_sso_start_url(next_path)
    if start:
        return redirect(start, code=302)
    return redirect(_redirect_target(), code=302)


@app.get("/healthz")
def healthz():
    return "ok", 200


@app.get("/auth/sso/callback")
def sso_callback():
    token = request.args.get("token", "")
    next_path = request.args.get("next", "/")
    if not next_path.startswith("/"):
        next_path = "/"
    try:
        claims = _verify_geohub_sso_token(token)
    except Exception as e:
        return f"SSO failed: {str(e)}", 401

    session["user"] = {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
    }

    base = NEXT_PUBLIC_DATALOGGER_URL.rstrip("/")
    if base:
        return redirect(f"{base}{next_path}", code=302)
    return redirect(next_path, code=302)


@app.get("/auth/logout")
def logout():
    session.clear()
    return redirect("/", code=302)


def _safe_unlink(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def _resolve_rig_number(raw_value: str | None) -> int:
    value = (raw_value or "").strip()
    if not value:
        return int(Config.RIG_NUMBER)
    if not value.isdigit():
        raise ValueError("Rig number must contain digits only.")
    return int(value)


def _build_sred_name(input_path: Path, rig_number: int) -> str:
    date_token = input_path.stem.split("_")[0]
    date_obj = datetime.strptime(date_token, "%Y%m%d")
    date_formatted = date_obj.strftime("%Y-%m-%d")
    ext = input_path.suffix.lower()
    return f"CS500-Novamac_{rig_number}_{date_formatted}T{ext}"


def _sharepoint_credentials_ok() -> bool:
    return bool(SP_SITE_URL and SP_DOC_LIBRARY and SP_CLIENT_ID and SP_CLIENT_SECRET)


def _upload_formatted_to_sharepoint(input_path: Path, rig_number: int):
    """
    Same naming and upload path as save_to_sred(), without mounts or delete/truncate.
    Uploads for any valid YYYYMMDD in the filename (Flask-only; production cron still uses save_to_sred's today rule).
    """
    if not _sharepoint_credentials_ok():
        return False, "SharePoint env vars missing (SP_SITE_URL, SP_DOC_LIBRARY, SP_CLIENT_ID, SP_CLIENT_SECRET)."

    p = input_path
    try:
        date_str = p.stem.split("_")[0]
        date = datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        return False, "Filename must start with YYYYMMDD (e.g. 20260309.csv)."
    date_formatted = date.strftime("%Y-%m-%d")
    ext = p.suffix.lower()
    if ext != ".csv":
        return False, "Only .csv files are supported for upload."

    processed_path: Path | None = None
    final_path: Path | None = None
    try:
        processed_path = Path(format_raw_file(p))
        new_name = f"CS500-Novamac_{rig_number}_{date_formatted}T{ext}"
        final_path = processed_path.with_name(new_name)
        os.replace(processed_path, final_path)

        ctx = ClientContext(SP_SITE_URL).with_credentials(
            ClientCredential(SP_CLIENT_ID, SP_CLIENT_SECRET)
        )
        folder = ctx.web.get_folder_by_server_relative_url(
            f"{SP_DOC_LIBRARY}/Data Logs/{rig_number}"
        )
        ctx.load(folder, ["Files"]).execute_query()

        if safe_upload_file(final_path, folder, new_name):
            return True, f"Uploaded to SharePoint as {new_name}."
        return False, "Upload failed (see server console for details)."
    except Exception as exc:
        return False, f"SharePoint error: {exc}"
    finally:
        _safe_unlink(input_path)
        if processed_path is not None:
            _safe_unlink(processed_path)
        if final_path is not None:
            _safe_unlink(final_path)


UPLOAD_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Drill data — CSV processor</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='sharepoint_upload.css') }}">
</head>
<body>
  <div class="page-shell">
    <div class="container">
      <header class="page-header">
        <div class="page-header-main">
          <img src="{{ url_for('static', filename='gs_logo.png') }}" alt="Geosource Energy" class="page-logo" width="160" height="40">
          <div class="page-title-block">
            <h1 class="page-title">Rig Data Logger Raw CSV Process and Upload Tool</h1>
            <p class="page-subtitle">Format raw rig CSVs and download or upload to SharePoint (local test tool).</p>
          </div>
        </div>
      </header>

      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          <div class="flash-messages">
            {% for category, message in messages %}
              <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <form method="post" enctype="multipart/form-data">
        <h2>Upload raw CSV</h2>
        <div class="form-group">
          <label for="raw_file">Select file</label>
          <input type="file" id="raw_file" name="raw_file" accept=".csv" required>
          <p class="hint">Filename must start with <code>YYYYMMDD</code> (e.g. <code>20260309.csv</code>). SharePoint upload accepts <strong>any</strong> valid date; the scheduled Pi job still uploads only same-day files.</p>
        </div>
        <div class="form-group">
          <label for="rig_number">Rig number (for SharePoint path and filename)</label>
          <input type="text" id="rig_number" name="rig_number" value="{{ rig_number }}" inputmode="numeric" pattern="[0-9]+">
          <p class="hint">Optional for download. For SharePoint uploads, enter the target rig number (digits only).</p>
        </div>
        <div class="btn-row">
          <button type="submit" name="action" value="download">Process and download</button>
          <button type="submit" name="action" value="sharepoint" class="btn-secondary">Process and upload to SharePoint</button>
        </div>
      </form>

    </div>
  </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def upload_and_process():
    rig_value = str(Config.RIG_NUMBER)
    if request.method == "POST":
        raw_file = request.files.get("raw_file")
        if not raw_file or not raw_file.filename:
            flash("Choose a CSV file to upload.", "error")
            return render_template_string(UPLOAD_FORM, rig_number=rig_value), 400

        safe_name = secure_filename(raw_file.filename)
        if not safe_name.lower().endswith(".csv"):
            flash("Only .csv files are supported.", "error")
            return render_template_string(UPLOAD_FORM, rig_number=rig_value), 400

        input_path = UPLOAD_DIR / safe_name
        raw_file.save(input_path)

        action = request.form.get("action") or "download"
        rig_value = (request.form.get("rig_number") or "").strip() or str(Config.RIG_NUMBER)
        try:
            rig_number = _resolve_rig_number(rig_value)
        except ValueError as exc:
            flash(str(exc), "error")
            _safe_unlink(input_path)
            return render_template_string(UPLOAD_FORM, rig_number=rig_value), 400

        if action == "sharepoint":
            ok, msg = _upload_formatted_to_sharepoint(input_path, rig_number)
            flash(msg, "success" if ok else "error")
            return render_template_string(UPLOAD_FORM, rig_number=rig_value)

        processed_path = Path(format_raw_file(input_path))
        output_name = _build_sred_name(input_path, rig_number)
        final_path = processed_path.with_name(output_name)
        os.replace(processed_path, final_path)

        @after_this_request
        def _cleanup_download_response(response):
            _safe_unlink(input_path)
            _safe_unlink(processed_path)
            _safe_unlink(final_path)
            return response

        return send_file(final_path, as_attachment=True, download_name=output_name)

    return render_template_string(UPLOAD_FORM, rig_number=rig_value)


if __name__ == "__main__":
    app.run(debug=True)
