"""Nalaganje konfiguracije.

Ključ: OPENAI_API_KEY iz .env (razvoj) ali iz APP_DIR/config.json (produkcija).
APP_DIR: Windows %APPDATA%\\Granola, macOS ~/Library/Application Support/Granola,
Linux ~/.config/Granola. config.json podpira polja: openai_api_key, drive_folder_id
(izrecen id obstoječe mape; sicer se mapa ustvari samodejno), docs_folder_name
(ime samodejne mape, privzeto "Granola zapiski"), calendar_id, poll_seconds.
"""

import json
import os
import sys
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv("GRANOVA_MODEL", "gpt-5.6-terra")


def _default_app_dir() -> Path:
    """Mapa za config/skrivnosti po navadah posameznega OS."""
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "Granola"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Granola"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return (Path(xdg) if xdg else Path.home() / ".config") / "Granola"


APP_DIR = _default_app_dir()
CONFIG_PATH = APP_DIR / "config.json"


@lru_cache(maxsize=1)
def load_config() -> dict:
    """Vrne vsebino APP_DIR/config.json (ali prazen dict)."""
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def get_setting(name: str, default=None):
    """Nastavitev iz config.json, z okoljem (GRANOVA_<NAME>) kot razvojno prednostjo."""
    env = os.getenv(f"GRANOVA_{name.upper()}")
    if env is not None:
        return env
    return load_config().get(name, default)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY") or load_config().get(
        "openai_api_key")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY ni nastavljen. Kopiraj .env.example v .env in vpiši ključ."
        )
    return OpenAI(api_key=api_key)
