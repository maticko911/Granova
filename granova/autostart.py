"""Samodejni zagon Granove ob prijavi v računalnik.

Windows: .cmd datoteka v mapi Startup (zažene pythonw, brez konzole).
macOS:   LaunchAgent plist v ~/Library/LaunchAgents + launchctl load.

Gradnja poti in vsebin je čista (testabilna brez pisanja na disk);
datoteke pišeta samo enable()/disable().
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ENTRY_NAME = "Granova"
LAUNCHAGENT_LABEL = "com.granova.app"


def repo_dir() -> Path:
    """Koren repozitorija (mapa z app.py)."""
    return Path(__file__).resolve().parent.parent


def entry_path(platform: str | None = None) -> Path:
    """Pot do zagonskega vnosa za dani OS (privzeto trenutni)."""
    platform = platform or sys.platform
    if platform == "win32":
        startup = (
            Path(os.environ.get("APPDATA", str(Path.home())))
            / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        )
        return startup / f"{ENTRY_NAME}.cmd"
    if platform == "darwin":
        return Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHAGENT_LABEL}.plist"
    raise NotImplementedError(f"Samodejni zagon za {platform} ni podprt")


def windows_cmd_content(repo: Path) -> str:
    """Vsebina .cmd: pythonw iz .venv, če obstaja, sicer sistemski."""
    return (
        "@echo off\r\n"
        f'cd /d "{repo}"\r\n'
        'if exist ".venv\\Scripts\\pythonw.exe" (\r\n'
        '  start "" ".venv\\Scripts\\pythonw.exe" app.py\r\n'
        ") else (\r\n"
        '  start "" pythonw app.py\r\n'
        ")\r\n"
    )


def launchagent_plist_content(repo: Path) -> str:
    """LaunchAgent plist: bash ovoj izbere .venv python3, če obstaja."""
    script = (
        f"cd '{repo}' && "
        "if [ -x .venv/bin/python3 ]; then exec .venv/bin/python3 app.py; "
        "else exec /usr/bin/env python3 app.py; fi"
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCHAGENT_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>{script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""


def is_enabled() -> bool:
    try:
        return entry_path().exists()
    except NotImplementedError:
        return False


def enable() -> Path:
    """Ustvari zagonski vnos in vrne njegovo pot."""
    path = entry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        path.write_text(windows_cmd_content(repo_dir()), encoding="utf-8")
    else:  # darwin (drugi OS-i padejo že v entry_path)
        path.write_text(launchagent_plist_content(repo_dir()), encoding="utf-8")
        subprocess.run(["launchctl", "load", str(path)], check=False,
                       capture_output=True)
    return path


def disable() -> None:
    """Odstrani zagonski vnos, če obstaja."""
    try:
        path = entry_path()
    except NotImplementedError:
        return
    if sys.platform == "darwin" and path.exists():
        subprocess.run(["launchctl", "unload", str(path)], check=False,
                       capture_output=True)
    path.unlink(missing_ok=True)
