#!/bin/bash
cd "$(dirname "$0")"

cd ..

rm -rf build dist/*

# Install needed dependencies
sudo apt-get update
sudo apt-get install python3-venv python3-dev python3-tk -y

printf "Creating virtual environment...\n\n"
python3 -m venv venv

printf "Activating virtual environment...\n\n"
source venv/bin/activate

printf "Update pip...\n\n"
python3 -m pip install --upgrade pip

printf "Install needed pip packages...\n\n"
python3 -m pip install -r requirements.txt

printf "Create app...\n\n"
pyinstaller eVAS.py \
            --onefile \
            --noconsole \
            --add-data 'images/:images/' \
            --hidden-import='PIL._tkinter_finder' \
            -n "eVAS_ubuntu" \
            -y

printf "Clean up...\n\n"
rm -r build
rm eVAS_ubuntu.spec
printf "Finished."
