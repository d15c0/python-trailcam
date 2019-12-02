#!/bin/bash
HOME_DIR="/home/pi/camera"
YEAR_DIR=$(date +%Y)
MONTH_DIR=$(date +%m)
DAY_DIR=$(date +%d)
START_DIR=$(date +%H_%M_%S)


sudo mkdir -p $HOME_DIR/$YEAR_DIR/$MONTH_DIR/$DAY_DIR/$START_DIR

sudo find $HOME_DIR -mtime +2 -exec rm -r -f {} \;

cd "${HOME_DIR}/${YEAR_DIR}/${MONTH_DIR}/${DAY_DIR}/${START_DIR}"

sudo python3 /<folder where python script is located>/python-trailcam.py 

