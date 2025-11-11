import os
import gc
from datetime import datetime

from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

from config import (
    SP_SITE_URL, SP_DOC_LIBRARY,
    SP_CLIENT_ID, SP_CLIENT_SECRET
)

from pathlib import Path
from process import file_formatted


def save_to_sred(files, rig=360):
    '''
    Upload exactly the file the user uploaded to SharePoint.
    - CSV -> Data/{rig}/
    - Others -> Reports/{rig}/
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

    # Stores existing filenames
    # existing = {f.properties["Name"] for f in folder.files}

    # Iterate through files and upload to SharePoint
    for file in files:
        try:
            p = file if isinstance(file, Path) else Path(file)
            filename = p.name
            date_str = p.stem

    # Extract filename which contains the date
            date = datetime.strptime(date_str, '%Y%m%d')
            date_formatted = date.strftime('%Y-%m-%d')
            ext = p.suffix.lower()
    # Format CSV file for Geometrics
            if (ext == ".csv"):
                file = file_formatted(p)

            new_name = f"CS500-Novamac_{rig}_{date_formatted}T{ext}"
            with open(p, 'rb') as file_obj:
                # Upload file to SharePoint
                if ('_uploaded' not in p.name):
                    folder.upload_file(new_name, file_obj).execute_query()
                else:
                    print(f"File {p.name} already uploaded to SharePoint")
            print(f"File {new_name} uploaded to SharePoint successfully")

            new_local_path = p.with_name(
                f"{date_formatted}_uploaded{ext}")
            if (new_local_path.exists()):
                print(f"File {p.name} already uploaded to SharePoint")
                continue
            p.rename(new_local_path)

            # Preparing new file name, if file already exists, add a number to the end
            # i = 1
            # Loop until name is unique in SharePoint folder
            # while new_name in existing:
            #     new_name = f"{new_name} ({i}){ext}"
            #     i += 1

            # Read file bytes and upload
            # data = file.read_bytes()  # Changed this method to streaming version below since files are large and we don't want to load all into memory

            # Removed since we are not holding the files in memory
            # del data
            # gc.collect()  # Force garbage collection after large file uploads (optional safeguard)

        except Exception as e:
            print(f"Error saving to SR&ED: {e}")

    print("File upload to sharepoint complete")
