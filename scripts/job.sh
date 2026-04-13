#!/bin/bash
set -e

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

USERNAME="${USERNAME:-dataloggerX}"
PROJECT_FOLDER="${PROJECT_FOLDER:-rig-data-logger}"

cd /home/$USERNAME/$PROJECT_FOLDER
source venv/bin/activate
python3 -m src.run_upload