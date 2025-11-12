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
from process import file_formatted


def delete_local_file(file):
    todayDate = datetime.now().strftime('%Y-%m-%d')
    file_date = file.name.split('_')[0]
    todayDate = datetime.strptime(todayDate, '%Y-%m-%d')
    file_date = datetime.strptime(file_date, '%Y-%m-%d')
    if (todayDate - file_date).days > 30:
        os.remove(file)
        print(f"File {file} deleted successfully")
    print(f"Done deleting files older than 30 days")

def safe_upload_file(file, folder,new_name, max_retries=3, retry_delay=5):
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



def save_to_sred(files, rig=360):
    '''
    Upload exactly the file the user uploaded to SharePoint.
    -> Reports/{rig}/
    '''
    print(f"Saving files to SharePoint for rig {rig}")

    # Authenticating with Sharepoint site using app credentials
    ctx = ClientContext(SP_SITE_URL).with_credentials(
        ClientCredential(SP_CLIENT_ID, SP_CLIENT_SECRET)
    )

    # Update folder and path in .env file after final file names are created
    folder = ctx.web.get_folder_by_server_relative_url(
        f"{SP_DOC_LIBRARY}/Reports/{rig}"
    )

    # Load existing files in the folder
    ctx.load(folder, ["Files"]).execute_query()


    # Iterate through files and upload to SharePoint
    for file in files:
        p = file if isinstance(file, Path) else Path(file)
        try:
            if ('_uploaded' in p.name):
                delete_local_file(p)
                print(f"File {p.name} already uploaded to SharePoint")
                continue
            date_str = p.stem

            # Extract filename which contains the date
            date = datetime.strptime(date_str, '%Y%m%d')
            date_formatted = date.strftime('%Y-%m-%d')
            ext = p.suffix.lower()

            # Format CSV file for Geometrics
            if (ext == ".csv"):
                file = file_formatted(p)
            else:
                print(f"File {p.name} is not a CSV file")

            # rename file to follow Danfoss convention for Geometrics processing
            new_name = f"CS500-Novamac_{rig}_{date_formatted}T{ext}"

            # Upload file to SharePoint if it hasn't been uploaded yet, use safe_upload_file function to handle retries
            attempt = safe_upload_file(p, folder, new_name)
            if (attempt):
                print(f"File {new_name} uploaded to SharePoint successfully")
            else:
                print(f"File {new_name} failed to upload to SharePoint")

            new_local_path = p.with_name(
                f"{date_formatted}_uploaded{ext}")

            if (new_local_path.exists()):
                print(f"File {p.name} already uploaded to SharePoint")
                continue
            p.rename(new_local_path)

        except Exception as e:
            print(f"Error saving to SR&ED: {e}")

    print("File upload to sharepoint complete")
