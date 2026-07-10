#!/bin/bash
# Zažene Granovo v menijski vrstici. Prvič: desni klik → Open.
cd "$(dirname "$0")"
if [ -x ".venv/bin/python3" ]; then
    nohup .venv/bin/python3 app.py >/dev/null 2>&1 &
else
    nohup python3 app.py >/dev/null 2>&1 &
fi
