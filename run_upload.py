import subprocess
from pathlib import Path
from sred_utils import save_to_sred
from flask import jsonify


def get_files_from_folder():
    # folder_path = r"C:\Users\DannyLiang-Geosource\Downloads\rig_test_folder"

    # File path for raspberry pi
    # folder_path = r"/home/admin/Downloads/rig_test_folder"
    folder_path = r"/media/username/BEA6-BBCE1/usb_share"

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

    # print(uploaded)
    return uploaded


def mount_drive():
    # Mount drive script path ONLY for raspberry pi
    mount_path = r"/home/username/Desktop/mountdrive.sh"
    mount_execute = subprocess.run(
        ["bash", mount_path], capture_output=True, text=True)
    if mount_execute.returncode != 0:
        raise Exception(f"Failed to mount drive: {mount_execute.stderr}")
    print("successfully mounted drive")


def unmount_drive():
    # Unmount drive script path ONLY for raspberry pi
    unmount_path = r"/home/username/Desktop/unmountdrive.sh"
    unmount_execute = subprocess.run(
        ["bash", unmount_path], capture_output=True, text=True)
    if unmount_execute.returncode != 0:
        raise Exception(f"Failed to unmount drive: {unmount_execute.stderr}")
    print("successfully unmounted drive") # for debugging in console


if __name__ == "__main__":
    mount_drive() # removed if not on raspberry pi
    files = get_files_from_folder()
    save_to_sred(files)
    unmount_drive() # removed if not on raspberry pi
