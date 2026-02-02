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
    #general
    USERNAME = "datalogger2"
    PROJECT_FOLDER = "pi-sharepoint-upload"  # name of project folder on Pi
    RIG_NUMBER = 365
    KEEP_DAYS = 30 #days to keep files on USB Stick before autodeleting 

    #usb drive
    USB_DEVICE = "/dev/sda1" #assumes stick is placed in bottom left
    USB_MOUNT = f"/media/{USERNAME}/usb_formatted_data"
    FORMATTED_DIR = USB_MOUNT

    #disk image file
    RIG_MOUNT = f"/mnt/raw_data" # Mount rig_data_container.bin here
    RAW_DIR = RIG_MOUNT # Raw CSV files will show up here!
    RIG_CONTAINER_FILE = f"/home/{USERNAME}/{PROJECT_FOLDER}/rig_data_container.bin" #virtual disk image

    #shell script file paths
    mount_usb_script = f"/home/{USERNAME}/{PROJECT_FOLDER}/mountdrive.sh"
    unmount_usb_script = f"/home/{USERNAME}/{PROJECT_FOLDER}/unmountdrive.sh"
    
    mount_image_script = f"/home/{USERNAME}/{PROJECT_FOLDER}/mountimage.sh"
    unmount_image_script = f"/home/{USERNAME}/{PROJECT_FOLDER}/unmountimage.sh"
     
    @classmethod
    def export_to_env(cls):
        #exports config. to environment variables so shell scripts can access them
        os.environ["USERNAME"] = cls.USERNAME
        os.environ["PROJECT_FOLDER"] = cls.PROJECT_FOLDER
        os.environ["USB_DEVICE"] = cls.USB_DEVICE
        os.environ["USB_MOUNT"] = cls.USB_MOUNT
        os.environ["RIG_CONTAINER_FILE"] = cls.RIG_CONTAINER_FILE
        os.environ["FORMATTED_DIR"] = cls.FORMATTED_DIR
        os.environ["RIG_MOUNT"] = cls.RIG_MOUNT
        os.environ["RAW_DIR"] = cls.RAW_DIR