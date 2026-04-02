import os
from pathlib import Path
from datetime import datetime

from flask import Flask, request, send_file, render_template_string
from werkzeug.utils import secure_filename

from config import Config
from process import format_raw_file

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = PROJECT_ROOT / "tmp_test_raw"
FORMATTED_DIR = PROJECT_ROOT / "tmp_test_formatted"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FORMATTED_DIR.mkdir(parents=True, exist_ok=True)

# Override formatted output path for this standalone local app.
Config.FORMATTED_DIR = str(FORMATTED_DIR)


def _build_sred_name(input_path: Path) -> str:
    date_token = input_path.stem.split("_")[0]
    date_obj = datetime.strptime(date_token, "%Y%m%d")
    date_formatted = date_obj.strftime("%Y-%m-%d")
    ext = input_path.suffix.lower()
    return f"CS500-Novamac_{Config.RIG_NUMBER}_{date_formatted}T{ext}"

UPLOAD_FORM = """
<!doctype html>
<title>Raw CSV Processor</title>
<h2>Upload Raw CSV</h2>
<form method="post" enctype="multipart/form-data">
  <input type="file" name="raw_file" accept=".csv" required />
  <button type="submit">Process file</button>
</form>
{% if output_name %}
  <p>Processed file: <strong>{{ output_name }}</strong></p>
  <a href="{{ url_for('download_processed', filename=output_name) }}">Download processed file</a>
{% endif %}
"""


@app.route("/", methods=["GET", "POST"])
def upload_and_process():
    output_name = None
    if request.method == "POST":
        raw_file = request.files.get("raw_file")
        if not raw_file or not raw_file.filename:
            return render_template_string(UPLOAD_FORM, output_name=None), 400

        safe_name = secure_filename(raw_file.filename)
        if not safe_name.lower().endswith(".csv"):
            return "Only .csv files are supported.", 400

        input_path = UPLOAD_DIR / safe_name
        raw_file.save(input_path)

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
