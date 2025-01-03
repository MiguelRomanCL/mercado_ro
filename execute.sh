#!/bin/bash
# Let's call this script venv.sh
source /home/ubuntu/mercado_ro/venv/bin/activate
python3 /home/ubuntu/mercado_ro/uso_estrategia_naive.py >> log.txt
sudo shutdown - h now
