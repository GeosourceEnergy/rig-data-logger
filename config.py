import os

#flask environment 
if os.environ.get("FLASK_ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

BASE_DIR           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_FILE_PATH = os.path.join(
    BASE_DIR,
    'REPORT_TEMPLATE.xlsx'
)

#sharepoint secret variables 
SP_SITE_URL      = os.getenv("SP_SITE_URL", "")
SP_DOC_LIBRARY   = os.getenv("SP_DOC_LIBRARY", "")
SP_CLIENT_ID     = os.getenv("SP_CLIENT_ID", "")
SP_CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET", "")
SP_TENANT_ID     = os.getenv("SP_TENANT_ID", "")

class Config:
    #variable variables... aha get the joke haha...
    USERNAME = "datalogger364"
    PROJECT_FOLDER = "pi-sharepoint-upload"  # name of project folder on Pi
    USB_ID = "D4C1-015C" #changes every time USB is formatted 
    USB_DEVICE = "/dev/sda1" #assumes stick is placed in bottom left Sss

    rig = 364

    #paths must match mountdrive.sh
    USB_MOUNT = f"/media/{USERNAME}/{USB_ID}"
    RAW_DIR = f"{USB_MOUNT}/raw"
    FORMATTED_DIR = f"{USB_MOUNT}/processed"
    
    #shell script file paths
    mount_script = f"/home/{USERNAME}/{PROJECT_FOLDER}/mountdrive.sh"
    unmount_script = f"/home/{USERNAME}/{PROJECT_FOLDER}/unmountdrive.sh"

    #NOTE: create your own paths/folders on PC for local testing 
     
    @classmethod
    def export_to_env(cls):
        #exports config. to environment variables so shell scripts can access them
        os.environ["USERNAME"] = cls.USERNAME
        os.environ["USB_DEVICE"] = cls.USB_DEVICE
        os.environ["USB_ID"] = cls.USB_ID
        os.environ["RAW_DIR"] = cls.RAW_DIR
        os.environ["FORMATTED_DIR"] = cls.FORMATTED_DIR