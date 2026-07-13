"""Enkratna nastavitev Google računa:

    python -m granova.setup_google

Koraki: client_secret.json (če manjka, terminalski čarovnik vodi skozi
Google Cloud Console — glej client_secret_wizard.py) → prijava v brskalniku
(token.json) → ustvari/najde skupno Drive mapo → zapiše preizkusni dokument,
da vizualno potrdiš delovanje pred pravim klicem. Ročna referenca:
SETUP_GOOGLE.md.
"""
from __future__ import annotations

import logging
import sys

from granova.auth import CLIENT_SECRET_PATH, get_credentials
from granova.config import get_setting
from granova.docs_writer import (
    DEFAULT_DOCS_FOLDER,
    create_doc,
    folder_link,
    get_or_create_folder,
)
from granova.models import MeetingNotes, MeetingResult, Objava


def _test_result() -> MeetingResult:
    return MeetingResult(
        notes=MeetingNotes(
            naslov="Preizkusni dokument",
            povzetek="Ta dokument je ustvarila Granova med nastavitvijo. "
                     "Če ga vidiš v skupni mapi, je vse pripravljeno — lahko ga izbrišeš.",
            kljucne_tocke=["Google prijava deluje", "Dokumenti se shranjujejo v skupno mapo"],
            odlocitve=[],
            naloge=[],
            udelezenci=[],
        ),
        objava=Objava(besedilo="(preizkus — tu bo osnutek objave)", predlogi=[]),
        enhanced_minutes="",
        transcript="(preizkus — tu bo celoten transkript sestanka)",
    )


def verify_google(creds) -> tuple[str, str]:
    """Najde/ustvari skupno mapo in zapiše preizkusni dokument.

    Vrne (povezava do mape, povezava do preizkusnega dokumenta).
    """
    folder_name = get_setting("docs_folder_name", DEFAULT_DOCS_FOLDER)
    folder_id = get_setting("drive_folder_id") or get_or_create_folder(creds, folder_name)
    doc_link = create_doc(creds, "Granova preizkus", _test_result())
    return folder_link(folder_id), doc_link


def run_google_setup(next_command: str = "python -m granova.setup_google") -> int:
    """Celoten Google del nastavitve; vrne 0 ob uspehu, 1 če manjka client_secret."""
    if not CLIENT_SECRET_PATH.exists():
        from granova.client_secret_wizard import run_wizard

        if not run_wizard():
            print(f"  Ko boš pripravljen(a), nastavitev nadaljuješ z: {next_command}")
            print("  (Ročna navodila za vse korake: SETUP_GOOGLE.md)")
            return 1
    else:
        print(f"✓ client_secret.json najden ({CLIENT_SECRET_PATH})")

    print("→ Prijava v Google (odpre se brskalnik, samo prvič) ...")
    creds = get_credentials()
    print("✓ Prijava uspešna, žeton shranjen")

    folder_url, doc_url = verify_google(creds)
    folder_name = get_setting("docs_folder_name", DEFAULT_DOCS_FOLDER)
    print(f"✓ Skupna mapa »{folder_name}«: {folder_url}")
    print(f"✓ Preizkusni dokument: {doc_url}")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    print("Granova — nastavitev Google računa\n")
    code = run_google_setup()
    if code == 0:
        print("\nVse pripravljeno! Odpri obe povezavi in preveri, da je dokument v mapi.")
        print("Preizkusni dokument lahko izbrišeš. Zdaj zaženi aplikacijo: python app.py")
    return code


if __name__ == "__main__":
    sys.exit(main())
