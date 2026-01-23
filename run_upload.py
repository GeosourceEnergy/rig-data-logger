import subprocess
from pathlib import Path
from sred_utils import save_to_sred
from config import Config
import sys


def get_files_from_folder():
    folder = Path(Config.RAW_DIR).expanduser().resolve()
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

#calls USB mount script
def mount_drive():
    Config.export_to_env()

    mount_execute = subprocess.run(
        ["bash", Config.mount_script], capture_output=True, text=True)
    
    if mount_execute.returncode != 0:
        raise Exception(f"Failed to mount drive: {mount_execute.stderr}")
    
    print("successfully mounted drive")

#calls USB unmount script
def unmount_drive():
    unmount_execute = subprocess.run(
        ["bash", Config.unmount_script], capture_output=True, text=True)
    if unmount_execute.returncode != 0:
        raise Exception(f"Failed to unmount drive: {unmount_execute.stderr}")
    print("successfully unmounted drive") # for debugging in console

#main function
def main():
    try:
        mount_drive()
        files = get_files_from_folder()
        
        if not files:
            print("no CSV files found")
            return
        
        print(f"found {len(files)} file(s)")

        save_to_sred(files)

        print("processing complete")

    except Exception as e:
        print(f"error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        try:
            unmount_drive()
        except Exception as e:
            print(f"error: {e}")





if __name__ == "__main__":
    main()
    
