#!/bin/bash

# stop on error
set -e

############################################################
# Functions                                                #
############################################################

# installs pandac 3.1.6.2 (AMD64)
function install_pandoc() {
    echo "Try to install pandoc it..."
    wget https://github.com/jgm/pandoc/releases/download/3.1.6.2/pandoc-3.1.6.2-1-amd64.deb
    dpkg -i pandoc-3.1.6.2-1-amd64.deb
    rm pandoc-3.1.6.2-1-amd64.deb
}

############################################################
# Main                                                     #
############################################################

# check and run only under ubuntu
if ! [  -n "$(uname -a | grep Linux)" ]; then
    echo "Please run the script under Linux (tested under Ubuntu). Terminating..."
    exit
fi  

# change working directory to location of script file
cd "$(dirname "$0")"

# Check if run as sudo
if [ "$(id -u)" -ne 0 ]; then echo "Please run as root." >&2; exit 1; fi

# install dependencies
echo "Installing dependencies..."
apt-get update -y
apt-get install git wget make fonts-hack-ttf -y

# install lexlive-full
echo "Installing texlive-full..."
apt-get install -y texlive-full

# clone the repository with build tools if not already done
git_folder="inara"
if [ ! -d "$git_folder" ] ; then
    echo "Cloning INARA git..."
    git clone https://github.com/openjournals/inara.git
fi

# if pandoc is not installed
echo "Checking pandoc..."
if ! [ -x "$(command -v pandoc)" ]; 
then
    echo "Pandoc is not installed."
    install_pandoc
else
    # if pandoc is insalled -> check version
    pandoc_version="$(pandoc --version)" 
    pandoc_version=${pandoc_version#*pandoc }   # remove prefix ending in "pandoc "
    pandoc_version=${pandoc_version%Features*}  # remove suffix starting with "Features"
    pandoc_version=${pandoc_version::-1}        # remove the last character - its a space

    if ! [ "$pandoc_version" = "3.1.6.2" ];
    then
        echo "Wrong pandoc version is currently installed."
        echo "Pandoc version":
        echo $pandoc_version
        install_pandoc
    else
        echo "Correct pandoc version already installed."
    fi
fi

# build the manuscript
echo "Build paper..."
cd inara
make pdf ARTICLE=../paper.md