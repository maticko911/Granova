"""Enkratna nastavitev Granove (vse na enem mestu):

    python -m granova.setup

Koraki: OpenAI ključ (vpiše se v APP_DIR/config.json, izven repozitorija) →
Google prijava + preizkusni dokument (glej SETUP_GOOGLE.md) → samodejni zagon
ob prijavi (privzeto vklopljen) → takojšen zagon v ozadju. Ponovni zagon je
varen — narejeni koraki se preskočijo.
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
    """Šifrirano zapiše ključ v APP_DIR/config.json (obstoječa polja ohrani)."""
    from granova.secrets_store import write_secret_text

    APP_DIR.mkdir(parents=True, exist_ok=True)
    data = load_config().copy()
    data["openai_api_key"] = key
    write_secret_text(CONFIG_PATH, json.dumps(data, indent=2))
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
        answer = input("→ Naj se Granova samodejno zažene ob vsaki prijavi (priporočeno)? [D/n] ").strip().lower()
        if answer in {"n", "ne", "no"}:
            print("  V redu — zaženeš jo ročno (Start Granova).")
        else:
            path = autostart.enable()
            print(f"✓ Samodejni zagon vklopljen ({path})")
            print("  (Kadarkoli ga izklopiš v meniju ikone Granove v sistemski vrstici.)")
    except NotImplementedError as exc:
        print(f"  ({exc})")


def _foreground_command() -> str:
    """Ukaz, ki app.py zažene v ospredju — napaka pade na zaslon, ne v dnevnik."""
    repo = autostart.repo_dir()
    if sys.platform == "win32":
        exe = repo / ".venv" / "Scripts" / "python.exe"
        return f'"{exe}" app.py' if exe.exists() else "python app.py"
    exe = repo / ".venv" / "bin" / "python3"
    return f"{exe} app.py" if exe.exists() else "python3 app.py"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    from granova import trust
    trust.install()  # zaupaj sistemski certifikatni shrambi (protivirusno HTTPS skeniranje)

    print("Granova — enkratna nastavitev\n")

    if not _step_openai():
        return 1
    print()
    if not _step_google():
        return 1
    print()
    _step_autostart()

    if autostart.launch_detached():
        print("\nVse pripravljeno! Granova zdaj teče v ozadju (glej ikono v sistemski vrstici)")
        print("  in se bo samodejno zagnala ob vsaki prijavi — terminala ni več treba odpirati.")
        print("  Ob vsakem Meet klicu posname, transkribira in zapiše Google Doc.")
        return 0

    # Nastavitev je shranjena, a zagon ni obstal — tega ne smemo zamolčati.
    print("\n✗ Nastavitev je shranjena, a Granova se ob zagonu ni obdržala.")
    print(f"  Vzrok je zapisan v: {autostart.startup_log_path()}")
    print("  Pošlji to datoteko razvijalcu — ali napako pokaži takoj z ukazom:")
    print(f"      {_foreground_command()}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
