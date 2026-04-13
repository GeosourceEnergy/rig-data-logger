#!/usr/bin/env bash
set -e

USERNAME="${USERNAME:-dataloggerX}"
PROJECT_FOLDER="${PROJECT_FOLDER:-rig-data-logger}"
cd "/home/${USERNAME}/${PROJECT_FOLDER}"

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt