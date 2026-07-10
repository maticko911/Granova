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

# Pomočnik za sistemski zvok (ScreenCaptureKit) — potrebuje Xcode ukazna orodja
if ! command -v swiftc >/dev/null 2>&1; then
    echo "Manjkajo Xcode ukazna orodja (swiftc). Namesti jih z ukazom:"
    echo "    xcode-select --install"
    echo "in po namestitvi še enkrat odpri setup.command."
    read -r -p "Pritisni Enter za konec ..."
    exit 1
fi
BIN_DIR="$HOME/Library/Application Support/Granola/bin"
mkdir -p "$BIN_DIR"
echo "Prevajam pomočnika za sistemski zvok ..."
if ! swiftc -O -framework ScreenCaptureKit -framework AVFoundation \
    -o "$BIN_DIR/granova-system-audio" \
    granova/audio_capture/mac_system_audio.swift; then
    echo "Prevajanje ni uspelo — potreben je macOS 13 ali novejši."
    read -r -p "Pritisni Enter za konec ..."
    exit 1
fi

echo
echo "Ob prvem snemanju bo macOS vprašal za dovoljenji 'Screen Recording' in"
echo "'Microphone' — potrdi ju in po potrebi enkrat znova zaženi Granovo."
echo

.venv/bin/python3 -m granova.setup
read -r -p "Pritisni Enter za konec ..."
