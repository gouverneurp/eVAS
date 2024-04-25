#!/bin/bash

# stop on error
set -e

############################################################
# Functions                                                #
############################################################

# blocking function that waits until "apt install" can be performed
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

# helper function that installs ubuntu packages but waits for other software managers to finish beforehand
function install() {
    echo "Try to install '$1'..."
    wait_until_free
    apt-get install "$1" -y
    echo "Finished installation."
    echo "____________________________________"
}

# installs pandac 3.1.6.2 (AMD64)
function install_pandoc() {
    echo "Try to install pandoc (3.1.6.2)..."
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
install git 
install wget 
install make 
install fonts-hack-ttf

# install lexlive-full
install texlive-full

# clone the repository with build tools if not already done
git_folder="inara"
if [ ! -d "$git_folder" ] ; then
    echo "Cloning INARA from GitHub..."
    git clone https://github.com/openjournals/inara.git
fi

# if pandoc is not installed
echo "Checking pandoc..."
if ! [ -x "$(command -v pandoc)" ]; 
then
    echo "Pandoc is not installed."
    install_pandoc
else
    # if pandoc is installed -> check version
    pandoc_version="$(pandoc --version)" 
    pandoc_version=${pandoc_version#*pandoc }   # remove prefix ending in "pandoc "
    pandoc_version=${pandoc_version%Features*}  # remove suffix starting with "Features"
    pandoc_version=${pandoc_version::-1}        # remove the last character - its a space

    if ! [ "$pandoc_version" = "3.1.6.2" ];
    then
        echo "Wrong pandoc version is currently installed."
        echo "Current installed pandoc version":
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