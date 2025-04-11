#!/bin/bash
# Let's call this script venv.sh
/home/ubuntu/mercado_ro/venv/bin/python3 /home/ubuntu/mercado_ro/uso_estrategia_naive.py >> /home/ubuntu/mercado_ro/log.txt 2>&1
sudo shutdown -h 1
