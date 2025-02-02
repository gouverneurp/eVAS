#!/bin/bash

# stop on error
set -e

cd "$(dirname "$0")"

cd ..

rm -rf build dist/*

printf "Creating virtual environment...\n\n"
python3 -m venv venv

printf "Activating virtual environment...\n\n"
source venv/bin/activate

printf "Update pip...\n\n"
python3 -m pip install --upgrade pip

printf "Install needed pip packages...\n\n"
python3 -m pip install -r requirements.txt

# apply MAC patch
# Fix 'Trouble with Permissions on Big Sur': https://github.com/moses-palmer/pynput/issues/416
# By: https://github.com/moses-palmer/pynput/pull/512
cp scripts/mac_patch/_darwin.py venv/lib/python3.12/site-packages/pynput/keyboard/

printf "Create app...\n\n"
pyinstaller eVAS.py \
            --clean \
            --onefile \
            --noconsole \
            --add-data 'images/:images/' \
            --icon='images/icon.ico' \
            --hidden-import='PIL._tkinter_finder' \
            -n "eVAS" \
            -y

printf "Clean up...\n\n"
rm -r build
rm eVAS.spec

printf "Finished."