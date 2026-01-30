import subprocess
from pathlib import Path
from sred_utils import save_to_sred
from config import Config
import sys
import os


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

#.BIN FILE IMAGE
def mount_image():
    Config.export_to_env()

    mount_execute = subprocess.run(
        ["bash", Config.mount_image_script], capture_output=True, text=True)
    
    if mount_execute.returncode != 0:
        raise Exception(f"Failed to mount drive: {mount_execute.stderr}")
    
    print("successfully mounted drive")

def unmount_image():
    unmount_execute = subprocess.run(
        ["bash", Config.unmount_image_script], capture_output=True, text=True)
    if unmount_execute.returncode != 0:
        raise Exception(f"Failed to unmount image: {unmount_execute.stderr}")
    print("successfully unmounted image") # for debugging in console

#USB DRIVE
def mount_usb_drive():
    Config.export_to_env()

    mount_execute = subprocess.run(
        ["bash", Config.mount_usb_script], capture_output=True, text=True)
    
    if mount_execute.returncode != 0:
        raise Exception(f"Failed to mount drive: {mount_execute.stderr}")
    
    print("successfully mounted drive")

#calls USB unmount script
def unmount_usb_drive():
    unmount_execute = subprocess.run(
        ["bash", Config.unmount_usb_script], capture_output=True, text=True)
    if unmount_execute.returncode != 0:
        raise Exception(f"Failed to unmount drive: {unmount_execute.stderr}")
    print("successfully unmounted drive") # for debugging in console


#main function - THIS IS WHAT RUNS!!!
def main():
    try:
        mount_image() 
        mount_usb_drive()
        files = get_files_from_folder()
        
        if not files:
            print("no CSV files found")
            return
        
        print(f"found {len(files)} file(s)")

        save_to_sred(files)

        print("processing complete")
        
        for file in files:
            file = Path(file)
            os.remove(file)

    except Exception as e:
        print(f"error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    
    
    finally:
        try:
            unmount_usb_drive()
            unmount_image() 
        except Exception as e:
            print(f"error: {e}")


if __name__ == "__main__":
    main()