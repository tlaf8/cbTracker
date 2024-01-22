#!/bin/bash

# Remove all old files
echo "--> purging old files"
rm -r pkg/*

# Download new files
echo "--> cloning new files"
git clone https://github.com/pakwan8/cbTracker /tmp/cbTracker

# Move new files into pkg and delete tmp
echo "--> moving new files"
mv /tmp/cbTracker/pkg/* pkg
yes | rm -r /tmp/cbTracker

# Recreate virtual env
echo "--> recreating virtual env"
cd pkg
python -m venv venv
venv/bin/pip install -r resources/requirements.txt

# chmod all .sh files
echo "--> setting execution permissions"
chmod +x run.sh

echo "--> finished"