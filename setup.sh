#!/bin/bash

shopt -s extglob

echo "Seeing if $HOME/Documents/cbTracker/ exists"
if [ ! -d "$HOME/Documents/cbTracker/" ]; then
  echo "Does not exist. Creating"
  mkdir $HOME/Documents/cbTracker
else
  rm -r $HOME/Documents/cbTracker/*
fi

echo "Copying files over"
cp -r !(setup.sh|.gitignore|__pycache__) $HOME/Documents/cbTracker

echo "Installing virtual environment and necessary libs"
cd $HOME/Documents/cbTracker
python -m venv venv
$HOME/Documents/cbTracker/venv/bin/python -m pip install --upgrade pip
$HOME/Documents/cbTracker/venv/bin/pip install -r resources/requirements.txt


echo "Creating desktop shortcut"
touch $HOME/Desktop/cbTracker.desktop
echo "" > $HOME/Desktop/cbTracker.desktop
echo "[Desktop Entry]" >> $HOME/Desktop/cbTracker.desktop
echo "Type=Application" >> $HOME/Desktop/cbTracker.desktop
echo "Version=1.0" >> $HOME/Desktop/cbTracker.desktop
echo "Name=cbTracker" >> $HOME/Desktop/cbTracker.desktop
echo "Comment=" >> $HOME/Desktop/cbTracker.desktop
echo "Exec=bash $HOME/Documents/cbTracker/run.sh" >> $HOME/Desktop/cbTracker.desktop
echo "Terminal=true" >> $HOME/Desktop/cbTracker.desktop
echo "Icon=$HOME/Documents/cbTracker/resources/img/icon.jpg" >> $HOME/Desktop/cbTracker.desktop

echo "Setting execution perms"
chmod +x $HOME/Desktop/cbTracker.desktop
chmod +x $HOME/Documents/cbTracker/run.sh

echo "Done"
echo ""
