"""Sistemsko obvestilo po shranjenih zapiskih — brez novih odvisnosti.

Windows: pystray Icon.notify (balon v sistemski vrstici). macOS: vgrajen
osascript `display notification` (pystray na darwin backend-u notify nima).
Obvestilo je pomožno: če spodleti, se obdelava ne sme podreti, zato
notify_saved nikoli ne vrže izjeme.
"""
from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def _esc(text: str) -> str:
    """Ubeži `\\` in `\"` za AppleScript literal v narekovajih."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def notify_saved(message: str, title: str = "Granova", tray=None) -> None:
    """Prikaže sistemsko obvestilo; ob kakršni koli napaki tiho odneha."""
    try:
        if sys.platform == "darwin":
            script = f'display notification "{_esc(message)}" with title "{_esc(title)}"'
            subprocess.run(
                ["osascript", "-e", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        elif sys.platform == "win32" and tray is not None:
            tray.notify(message, title)
    except Exception:
        logger.exception("Sistemsko obvestilo ni uspelo — nadaljujem brez njega")
