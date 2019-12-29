#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /
cd home/pi/bbt
sudo python3 /home/pi/Desktop/26_final/flow_meter.py
cd /
