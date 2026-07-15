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

# Koliko časa po zagonu počakamo, da vidimo, ali je proces obstal ali umrl.
# Uvoz knjižnic + tk okno sta na počasnem disku lahko sekundo ali dve.
STARTUP_GRACE_SECONDS = 3.0


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
    """LaunchAgent plist: bash ovoj izbere .venv python3, če obstaja.

    Izpis speljemo v dnevnik: launchd ga sicer vrže v nič in zlom ob prijavi
    ne pusti nobene sledi — videti je, kot da se aplikacija »ni zagnala«.
    """
    script = (
        f"cd '{repo}' && "
        "if [ -x .venv/bin/python3 ]; then exec .venv/bin/python3 app.py; "
        "else exec /usr/bin/env python3 app.py; fi"
    )
    log = repo / "data" / "granova-startup.log"
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
    <key>StandardOutPath</key>
    <string>{log}</string>
    <key>StandardErrorPath</key>
    <string>{log}</string>
</dict>
</plist>
"""


def _run_python(gui: bool = True, platform: str | None = None) -> str:
    """Pot do interpreterja za zagon app.py (ista logika kot zagonske skripte).

    gui=True na Windows izbere pythonw (brez konzolnega okna).
    """
    platform = platform or sys.platform
    repo = repo_dir()
    if platform == "win32":
        name = "pythonw" if gui else "python"
        venv = repo / ".venv" / "Scripts" / f"{name}.exe"
        return str(venv) if venv.exists() else name
    venv = repo / ".venv" / "bin" / "python3"
    return str(venv) if venv.exists() else "python3"


def startup_log_path() -> Path:
    """Dnevnik zgodnjega zagona — stdout/stderr novo zagnanega procesa."""
    from granova.config import APP_DIR

    return APP_DIR / "granova-startup.log"


def _open_startup_log():
    try:
        path = startup_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        return open(path, "a", encoding="utf-8", errors="replace")
    except OSError:
        return None


def launch_detached(grace_seconds: float = STARTUP_GRACE_SECONDS) -> bool:
    """Zažene Granovo kot proces, neodvisen od terminala. Vrne True le, če živi.

    Preživi zaprtje terminala/konzole; morebitno podvojitev prepreči varovalo
    v app.py (single_instance).

    Zgodnji zlom (manjkajoča odvisnost, napaka ob uvozu) se drugače izgubi:
    proces se splodi, takoj umre, klicatelj pa javi uspeh — stranka prebere
    »teče v ozadju«, v resnici pa ne teče nič. Zato gresta stdout in stderr v
    `startup_log_path()` (namesto v DEVNULL), tu pa počakamo `grace_seconds` in
    vrnemo False, če proces v tem času umre. Dnevnik takrat pove, zakaj.
    """
    try:
        repo = repo_dir()
        log = _open_startup_log()
        out = log or subprocess.DEVNULL
        err = subprocess.STDOUT if log else subprocess.DEVNULL
        try:
            if sys.platform == "win32":
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                proc = subprocess.Popen(
                    [_run_python(gui=True), "app.py"],
                    cwd=str(repo),
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    close_fds=True,
                    stdout=out,
                    stderr=err,
                )
            else:
                proc = subprocess.Popen(
                    [_run_python(gui=True), "app.py"],
                    cwd=str(repo),
                    start_new_session=True,
                    stdout=out,
                    stderr=err,
                )
        finally:
            if log:
                log.close()  # cev ostane odprta v otroku
    except Exception:
        return False

    try:
        proc.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        return True  # še vedno teče — zagon je obstal
    return False  # umrl med zagonom; vzrok je v startup dnevniku


def is_enabled() -> bool:
    try:
        return entry_path().exists()
    except NotImplementedError:
        return False


def refresh() -> bool:
    """Poravna obstoječi zagonski vnos s trenutno mapo aplikacije.

    Vnos hrani absolutno pot do mape; če se mapa premakne ali preimenuje,
    star vnos ob prijavi tiho odpove (cd na neobstoječo mapo, brez okna in
    brez napake). Vrne True, če je bil vnos znova zapisan.
    """
    try:
        path = entry_path()
    except NotImplementedError:
        return False
    if not path.exists():
        return False  # samodejni zagon ni vključen — ne vklapljaj ga sam
    expected = (
        windows_cmd_content(repo_dir()) if sys.platform == "win32"
        else launchagent_plist_content(repo_dir())
    )
    try:
        current = path.read_text(encoding="utf-8")
    except OSError:
        current = ""
    # primerjava neodvisno od vrste prelomov vrstic (\r\n proti \n)
    def _norm(s: str) -> str:
        return s.replace("\r\n", "\n").replace("\r", "\n")

    if _norm(current) == _norm(expected):
        return False
    enable()
    return True


def enable() -> Path:
    """Ustvari zagonski vnos in vrne njegovo pot."""
    path = entry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        # newline="" — brez prevajanja, da \r\n ne postane \r\r\n
        path.write_text(windows_cmd_content(repo_dir()), encoding="utf-8", newline="")
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
