"""Nalaganje konfiguracije.

Ključ: OPENAI_API_KEY iz .env (razvoj) ali iz APP_DIR/config.json (produkcija).
APP_DIR: podatkovna mapa `data/` znotraj mape aplikacije. Vse skrivnosti (ključ,
Google client_secret.json in token.json) živijo tu, zato izbris mape aplikacije
zbriše tudi njih — stranka mora ob ponovni uporabi vnesti nov ključ in znova
odobriti Google. Pot je mogoče prepisati z okoljsko GRANOVA_DATA_DIR.
config.json podpira polja: openai_api_key, drive_folder_id (izrecen id obstoječe
mape; sicer se mapa ustvari samodejno), docs_folder_name (ime samodejne mape,
privzeto "Granola zapiski"), calendar_id, poll_seconds.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv("GRANOVA_MODEL", "gpt-5.6-terra")


def _default_app_dir() -> Path:
    """Podatkovna mapa znotraj aplikacije, da izbris mape zbriše tudi skrivnosti."""
    override = os.environ.get("GRANOVA_DATA_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "data"


APP_DIR = _default_app_dir()
CONFIG_PATH = APP_DIR / "config.json"


@lru_cache(maxsize=1)
def load_config() -> dict:
    """Vrne vsebino APP_DIR/config.json (ali prazen dict). Datoteka je šifrirana."""
    from granova.secrets_store import read_secret_text

    try:
        text = read_secret_text(CONFIG_PATH)
        return json.loads(text) if text else {}
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
