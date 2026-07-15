#!/bin/bash
# Zažene Granovo v menijski vrstici. Prvič: desni klik → Open.
cd "$(dirname "$0")"
# Izpis gre v dnevnik, ne v /dev/null — sicer se zlom ob zagonu tiho izgubi.
mkdir -p data
LOG="data/granova-startup.log"
if [ -x ".venv/bin/python3" ]; then
    nohup .venv/bin/python3 app.py >>"$LOG" 2>&1 &
else
    nohup python3 app.py >>"$LOG" 2>&1 &
fi
