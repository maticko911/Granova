#!/bin/bash
# Granova — enkratna nastavitev (macOS). Dvoklikni to datoteko
# (prvič: desni klik → Open, ker aplikacija ni podpisana).
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 ni nameščen. Prenesi ga s https://www.python.org/downloads/ in ponovi."
    read -r -p "Pritisni Enter za konec ..."
    exit 1
fi

if [ ! -x ".venv/bin/python3" ]; then
    echo "Pripravljam okolje ..."
    python3 -m venv .venv
fi

echo "Nameščam knjižnice ..."
.venv/bin/python3 -m pip install -q -r requirements.txt || \
.venv/bin/python3 -m pip install -q -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

.venv/bin/python3 -m granova.setup
read -r -p "Pritisni Enter za konec ..."
