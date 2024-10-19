#!/bin/bash

shopt -s extglob

cd $HOME/Documents/cbTracker/
echo "Program will run in 5 seconds..."
read -t 5 -p "Update? (y/n) " update
if [ "$update" = "y" ]; then
    echo "Purging old files"
    if [ -z "$(ls $HOME/Documents/cbTracker)" ]; then
        rm -r $HOME/Documents/cbTracker/!(venv|run.sh)
    fi

    echo "Downloading new files"
    if [ -d "/tmp/cbTracker" ]; then
        yes | rm -r /tmp/cbTracker
    fi

    git clone https://github.com/pakwan8/cbTracker.git /tmp/cbTracker
    cp -r /tmp/cbTracker/!(run.sh|setup.sh) .

    if [ -f "$HOME/Documents/cbTracker/resources/requirements.txt" ]; then
        venv/bin/pip install --upgrade pip
        venv/bin/pip install -r resources/requirements.txt
    else
        echo "Files were not copied properly. Aborting and try running again."
    fi

    echo "Update complete. Starting program..."
    sleep 5
    venv/bin/python main.py

else
    venv/bin/python main.py
fi
