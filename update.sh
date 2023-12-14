#!/bin/bash

# Move auth and validation
mv pkg/resources/data/api_key.json pkg/resources/data/validation.json .

# Remove all old files
rm -r pkg/*

# Download new files
git clone https://github.com/pakwan8/cbTracker /tmp/cbTracker

# Move new files into pkg and delete tmp
mv /tmp/cbTracker/pkg/* pkg
yes | rm -r /tmp/cbTracker

# Move validation and auth back
mv validation.json api_key.json pkg/resources/data

echo finished