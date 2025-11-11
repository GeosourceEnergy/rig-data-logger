import os
import logging
from flask import (
    redirect,
    url_for, flash,
    Blueprint, render_template,
)



from pathlib import Path
from sred_utils import save_to_sred

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


# Function that gets files from local folder
@main_bp.route('/files/list', methods=['GET'])
def get_files_from_folder():
    folder_path = r"C:\Users\DannyLiang-Geosource\Downloads\rig_test_folder"
    # folder_path = r"/home/admin/Downloads/rig_test_folder"
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists():
        raise FileNotFoundError(f"Folder {folder} does not exist")
    if not folder.is_dir():
        raise NotADirectoryError(f"Folder {folder} is not a directory")
    allowed_ext = {".csv"}
    uploaded = []

    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in allowed_ext:
            uploaded.append(file)

    print(uploaded)  # for debugging in console
    return uploaded


@main_bp.route('/save_report_sred', methods=['POST'])
def run_folder_batch():
    try:
        # 1) get everything in the folder
        files = get_files_from_folder()
        uploaded = save_to_sred(files)  # 2) iterate & upload

        msg = [f"Uploaded {uploaded}"]
        flash(" | ".join(msg), "success")
    except Exception as e:
        logging.exception("Batch upload failed")
        flash(f"Batch upload failed: {e}", "error")
    return redirect(url_for('main.index'))
