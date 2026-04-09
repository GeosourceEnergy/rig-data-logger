#!/usr/bin/env bash
set -e

RIG_NUMBER="${RIG_NUMBER:-999}"
USERNAME="${USERNAME:-datalogger${RIG_NUMBER}}"
PROJECT_FOLDER="${PROJECT_FOLDER:-pi-sharepoint-upload}"
cd "/home/${USERNAME}/${PROJECT_FOLDER}"

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt