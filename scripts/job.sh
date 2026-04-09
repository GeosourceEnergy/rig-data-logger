#!/bin/bash
set -e

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RIG_NUMBER="${RIG_NUMBER:-999}"
USERNAME="${USERNAME:-datalogger${RIG_NUMBER}}"
PROJECT_FOLDER="${PROJECT_FOLDER:-pi-sharepoint-upload}"

cd /home/$USERNAME/$PROJECT_FOLDER
source venv/bin/activate
python3 src/run_upload.py