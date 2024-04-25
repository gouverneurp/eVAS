#!/bin/bash

# stop on error
set -e

############################################################
# Functions                                                #
############################################################

function wait_until_free() {
    i=0
    tput sc
    while sudo fuser /var/{lib/{dpkg,apt/lists},cache/apt/archives}/lock >/dev/null 2>&1; do
        case $(($i % 4)) in
            0 ) j="-" ;;
            1 ) j="\\" ;;
            2 ) j="|" ;;
            3 ) j="/" ;;
        esac
        tput rc
        echo -en "\r[$j] Waiting for other software managers to finish..." 
        sleep 0.5
        ((i=i+1))
    done 
}

function install() {
    echo "Try to install '$1'..."
    wait_until_free
    sudo apt-get install "$1" -y
    echo "Finished installation."
    echo "____________________________________"
}

############################################################
# Main                                                     #
############################################################

cd "$(dirname "$0")"

cd ..

rm -rf build dist/*

# Install needed dependencies
sudo apt-get update
install python3-venv 
install python3-dev 
install python3-tk

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
