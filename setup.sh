#!/bin/bash

echo "--> seeing if $HOME/Documents/cbTracker/ exists"
if [ ! -d "$HOME/Documents/cbTracker/" ]; then
  echo "does not exist. Creating"
  mkdir $HOME/Documents/cbTracker
fi

echo "--> copying files over"
cp -r pkg/* $HOME/Documents/cbTracker

echo "--> installing virtual environment and necessary libs"
cd $HOME/Documents/cbTracker
python -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/pip install -r resources/requirements.txt


echo "--> creating desktop shortcut"

touch $HOME/Desktop/cbTracker.desktop
echo "" > $HOME/Desktop/cbTracker.desktop
echo "[Desktop Entry]" >> $HOME/Desktop/cbTracker.desktop
echo "Type=Application" >> $HOME/Desktop/cbTracker.desktop
echo "Version=1.0" >> $HOME/Desktop/cbTracker.desktop
echo "Name=cbTracker" >> $HOME/Desktop/cbTracker.desktop
echo "Comment=" >> $HOME/Desktop/cbTracker.desktop
echo "Exec=bash $HOME/Documents/cbTracker/run.sh && read -n 1 -s -r -p 'Press any key to continue'" >> $HOME/Desktop/cbTracker.desktop
echo "Terminal=true" >> $HOME/Desktop/cbTracker.desktop
echo "Icon=$HOME/Documents/cbTracker/resources/img/scan_img.jpg" >> $HOME/Desktop/cbTracker.desktop

chmod +x $HOME/Desktop/cbTracker.desktop

printf "\n--> done\n"
