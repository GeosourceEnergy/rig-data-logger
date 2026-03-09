import os
import gc
from datetime import datetime
import time

from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

from config import (
    SP_SITE_URL, SP_DOC_LIBRARY,
    SP_CLIENT_ID, SP_CLIENT_SECRET
)

from pathlib import Path
from process import format_raw_file
from config import Config

def delete_old_files():
    today_date = datetime.strptime(datetime.now().strftime('%Y%m%d'), '%Y%m%d')
    formatted_folder = Path(Config.FORMATTED_DIR)
    raw_folder = Path(Config.RAW_DIR)

    #formatted files
    if not formatted_folder.exists():
        raise FileNotFoundError(f"Folder {formatted_folder} does not exist")
    for file in formatted_folder.iterdir():
        file_date = datetime.strptime(file.stem.split('_')[0], '%Y%m%d')
        if ("_formatted" in file.stem and (today_date - file_date).days > Config.KEEP_DAYS):
            os.remove(file)
            print(f"File {file} deleted successfully")

    #raw files
    if not raw_folder.exists():
        raise FileNotFoundError(f"Folder {raw_folder} does not exist")
    for file in raw_folder.iterdir():
        if file.suffix != '.csv':
            continue
        file_date = datetime.strptime(file.stem.split('_')[0], '%Y%m%d')
        if ((today_date - file_date).days > Config.KEEP_DAYS):
            os.remove(file)
            print(f"File {file} deleted successfully")
    print(f"Done deleting files older than {Config.KEEP_DAYS} days")


def safe_upload_file(file, folder, new_name, max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            with open(file, 'rb') as file_obj:
                folder.upload_file(new_name, file_obj).execute_query()
            print(f"File {new_name} uploaded to SharePoint successfully")
            return True
        except Exception as e:
            print(f"Error uploading file {file}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * attempt)
            else:
                raise e
    return False


def save_to_sred(files):
    '''
    Upload exactly the file the user uploaded to SharePoint.
    -> Reports/{rig}/
    '''
    print(f"Saving files to SharePoint for rig {Config.RIG_NUMBER}")

    # Authenticating with Sharepoint site using app credentials
    ctx = ClientContext(SP_SITE_URL).with_credentials(
        ClientCredential(SP_CLIENT_ID, SP_CLIENT_SECRET)
    )

    # Update folder and path in .env file after final file names are created
    folder = ctx.web.get_folder_by_server_relative_url(
        f"{SP_DOC_LIBRARY}/Reports/{Config.RIG_NUMBER}"
    )

    # Load existing files in the folder
    ctx.load(folder, ["Files"]).execute_query()

    # keep only csv files

    # Iterate through files and upload to SharePoint
    for file in files:
        p = file if isinstance(file, Path) else Path(file)
        try:
            date_str = p.stem

            # Extract filename which contains the date
            date = datetime.strptime(date_str, '%Y%m%d')
            date_formatted = date.strftime('%Y-%m-%d')
            ext = p.suffix.lower()

            # Format CSV file for Geometrics
            if (ext == ".csv"):
                file = format_raw_file(p)
            else:
                print(f"File {p.name} is not a CSV file")

            # rename file to follow Danfoss convention for Geometrics processing
            new_name = f"CS500-Novamac_{Config.RIG_NUMBER}_{date_formatted}T{ext}"

            # Upload file to SharePoint if it hasn't been uploaded yet, use safe_upload_file function to handle retries
            today_date = datetime.strptime(datetime.now().strftime('%Y%m%d'), '%Y%m%d')
            # if ("20251008" == date_str): # for local testing
            if (today_date == date): # only upload files from today 
                attempt = safe_upload_file(file, folder, new_name)
                if (attempt):
                    print(f"File {new_name} uploaded to SharePoint successfully")

            

        except Exception as e:
            print(f"Error saving to SR&ED: {e}")
            
    delete_old_files()

    print("File upload to sharepoint complete")
