import os
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, request, send_file, render_template_string, flash
from werkzeug.utils import secure_filename

from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

from config import Config
from config import SP_SITE_URL, SP_DOC_LIBRARY, SP_CLIENT_ID, SP_CLIENT_SECRET
from src.process import format_raw_file
from src.sred_utils import safe_upload_file

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-local-only-change-me")

PROJECT_ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = PROJECT_ROOT / "tmp_test_raw"
FORMATTED_DIR = PROJECT_ROOT / "tmp_test_formatted"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FORMATTED_DIR.mkdir(parents=True, exist_ok=True)

# Override formatted output path for this standalone local app.
Config.FORMATTED_DIR = str(FORMATTED_DIR)


def _cleanup_temp_dirs(keep_days: int = 14) -> None:
    cutoff = datetime.now() - timedelta(days=keep_days)
    for folder in (UPLOAD_DIR, FORMATTED_DIR):
        for file in folder.iterdir():
            if not file.is_file():
                continue
            modified_at = datetime.fromtimestamp(file.stat().st_mtime)
            if modified_at < cutoff:
                try:
                    file.unlink()
                except OSError:
                    # Best-effort cleanup; skip locked/in-use files.
                    continue


def _build_sred_name(input_path: Path) -> str:
    date_token = input_path.stem.split("_")[0]
    date_obj = datetime.strptime(date_token, "%Y%m%d")
    date_formatted = date_obj.strftime("%Y-%m-%d")
    ext = input_path.suffix.lower()
    return f"CS500-Novamac_{Config.RIG_NUMBER}_{date_formatted}T{ext}"


def _sharepoint_credentials_ok() -> bool:
    return bool(SP_SITE_URL and SP_DOC_LIBRARY and SP_CLIENT_ID and SP_CLIENT_SECRET)


def _upload_formatted_to_sharepoint(input_path: Path):
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

    try:
        processed_path = Path(format_raw_file(p))
        new_name = f"CS500-Novamac_{Config.RIG_NUMBER}_{date_formatted}T{ext}"
        final_path = processed_path.with_name(new_name)
        os.replace(processed_path, final_path)

        ctx = ClientContext(SP_SITE_URL).with_credentials(
            ClientCredential(SP_CLIENT_ID, SP_CLIENT_SECRET)
        )
        folder = ctx.web.get_folder_by_server_relative_url(
            f"{SP_DOC_LIBRARY}/Data Logs/{Config.RIG_NUMBER}"
        )
        ctx.load(folder, ["Files"]).execute_query()

        if safe_upload_file(final_path, folder, new_name):
            return True, f"Uploaded to SharePoint as {new_name}."
        return False, "Upload failed (see server console for details)."
    except Exception as exc:
        return False, f"SharePoint error: {exc}"


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
        <div class="btn-row">
          <button type="submit" name="action" value="download">Process and download</button>
          <button type="submit" name="action" value="sharepoint" class="btn-secondary">Process and upload to SharePoint</button>
        </div>
      </form>

      {% if output_name %}
      <div class="results-section">
        <h3>Ready to download</h3>
        <p class="file-name">{{ output_name }}</p>
        <p><a href="{{ url_for('download_processed', filename=output_name) }}">Download processed file</a></p>
      </div>
      {% endif %}
    </div>
  </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def upload_and_process():
    output_name = None
    if request.method == "POST":
        _cleanup_temp_dirs()
        raw_file = request.files.get("raw_file")
        if not raw_file or not raw_file.filename:
            flash("Choose a CSV file to upload.", "error")
            return render_template_string(UPLOAD_FORM, output_name=None), 400

        safe_name = secure_filename(raw_file.filename)
        if not safe_name.lower().endswith(".csv"):
            flash("Only .csv files are supported.", "error")
            return render_template_string(UPLOAD_FORM, output_name=None), 400

        input_path = UPLOAD_DIR / safe_name
        raw_file.save(input_path)

        action = request.form.get("action") or "download"

        if action == "sharepoint":
            ok, msg = _upload_formatted_to_sharepoint(input_path)
            flash(msg, "success" if ok else "error")
            output_name = _build_sred_name(input_path) if ok else None
            return render_template_string(UPLOAD_FORM, output_name=output_name)

        processed_path = Path(format_raw_file(input_path))
        output_name = _build_sred_name(input_path)
        final_path = processed_path.with_name(output_name)
        os.replace(processed_path, final_path)

    return render_template_string(UPLOAD_FORM, output_name=output_name)


@app.route("/download/<path:filename>", methods=["GET"])
def download_processed(filename):
    safe_name = secure_filename(filename)
    target = FORMATTED_DIR / safe_name
    if not target.exists():
        return "Processed file not found.", 404
    return send_file(target, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
