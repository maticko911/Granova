"""Enkratna nastavitev Granove (vse na enem mestu):

    python -m granova.setup

Koraki: OpenAI ključ (vpiše se v APP_DIR/config.json, izven repozitorija) →
Google prijava + preizkusni dokument (glej SETUP_GOOGLE.md) → neobvezni
samodejni zagon ob prijavi. Ponovni zagon je varen — narejeni koraki se preskočijo.
"""
from __future__ import annotations

import json
import logging
import os
import sys

from granova.config import APP_DIR, CONFIG_PATH, load_config
from granova import autostart
from granova.auth import TOKEN_PATH
from granova.setup_google import run_google_setup


def _save_openai_key(key: str) -> None:
    """Zapiše ključ v APP_DIR/config.json (obstoječa polja ohrani)."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    data = load_config().copy()
    data["openai_api_key"] = key
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    load_config.cache_clear()


def _step_openai() -> bool:
    if os.getenv("OPENAI_API_KEY") or load_config().get("openai_api_key"):
        print("✓ OpenAI ključ je že nastavljen")
        return True
    print("→ OpenAI ključ še ni nastavljen.")
    print("  Najdeš ga na https://platform.openai.com/api-keys (začne se s sk-...)")
    key = input("  Prilepi ključ in pritisni Enter: ").strip()
    if not key.startswith("sk-"):
        print("✗ To ne izgleda kot OpenAI ključ — ponovno zaženi: python -m granova.setup")
        return False
    _save_openai_key(key)
    print(f"✓ Ključ shranjen v {CONFIG_PATH} (izven repozitorija, ne gre na GitHub)")
    return True


def _step_google() -> bool:
    if TOKEN_PATH.exists():
        print(f"✓ Google je že prijavljen ({TOKEN_PATH})")
        return True
    return run_google_setup(next_command="python -m granova.setup") == 0


def _step_autostart() -> None:
    try:
        if autostart.is_enabled():
            print("✓ Samodejni zagon ob prijavi je že vklopljen")
            return
        answer = input("→ Naj se Granova zažene samodejno ob prijavi v računalnik? [d/n] ").strip().lower()
        if answer in {"d", "da", "y", "yes"}:
            path = autostart.enable()
            print(f"✓ Samodejni zagon vklopljen ({path})")
        else:
            print("  V redu — zaženeš jo ročno (Start Granova).")
    except NotImplementedError as exc:
        print(f"  ({exc})")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    print("Granova — enkratna nastavitev\n")

    if not _step_openai():
        return 1
    print()
    if not _step_google():
        return 1
    print()
    _step_autostart()

    print("\nVse pripravljeno! Granova zdaj deluje samodejno:")
    print("  zaženi jo (Start Granova ali: python app.py) in pusti v sistemski vrstici —")
    print("  ob vsakem Meet klicu posname, transkribira in zapiše Google Doc.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
