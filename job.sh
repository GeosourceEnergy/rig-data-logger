set -e

USERNAME="${USERNAME:-datalogger364}"
PROJECT_FOLDER="${PROJECT_FOLDER:-pi-sharepoint-upload}"

cd /home/$USERNAME/$PROJECT_FOLDER
source venv/bin/activate
python3 run_upload.py