"""Terminalski čarovnik za pridobitev client_secret.json.

Netehnično stranko vodi skozi Google Cloud Console korak za korakom (vsak
korak sam odpre pravo stran v brskalniku), nato sprejme datoteko na tri
načine: prazen Enter (samodejno iskanje v mapi Prenosi/Downloads), povlečena
datoteka v okno terminala (pot) ali prilepljena vsebina JSON. Veljavno
vsebino shrani v APP_DIR/client_secret.json in vrne True — setup se nadaljuje
brez ponovnega zagona. Ročna referenca ostaja SETUP_GOOGLE.md.
"""
from __future__ import annotations

import json
import webbrowser
from pathlib import Path

from granova.auth import CLIENT_SECRET_PATH

# (naslov, navodila, seznam strani, ki se odprejo v brskalniku)
STEPS: list[tuple[str, str, list[str]]] = [
    (
        "Nov projekt",
        "Če te vpraša, se prijavi s svojim Google računom.\n"
        "  Ime projekta: Granova → klikni »Create« → počakaj nekaj sekund,\n"
        "  nato zgoraj levo v izbirniku projektov izberi »Granova«.",
        ["https://console.cloud.google.com/projectcreate"],
    ),
    (
        "Vklopi tri API-je",
        "Odprle so se tri strani (Docs, Drive, Calendar) — na vsaki klikni\n"
        "  moder gumb »Enable« in počakaj, da se stran osveži.",
        [
            "https://console.cloud.google.com/apis/library/docs.googleapis.com",
            "https://console.cloud.google.com/apis/library/drive.googleapis.com",
            "https://console.cloud.google.com/apis/library/calendar-json.googleapis.com",
        ],
    ),
    (
        "Zaslon za soglasje (OAuth consent screen)",
        "Tip: »External« → »Create«. Ime aplikacije: Granova; support e-pošta:\n"
        "  tvoj naslov; ostalo pusti prazno in shranjuj naprej. Pri »Test users«\n"
        "  klikni »Add users« in dodaj svoj Google e-naslov → shrani.",
        ["https://console.cloud.google.com/apis/credentials/consent"],
    ),
    (
        "Poverilnice (Desktop app) + prenos datoteke",
        "Application type: »Desktop app«, ime: Granova → »Create«.\n"
        "  V okencu, ki se pokaže, klikni »Download JSON« — datoteka se shrani\n"
        "  v mapo Prenosi (Downloads).",
        ["https://console.cloud.google.com/auth/clients/create"],
    ),
]


def validate_client_secret(text: str) -> tuple[bool, str]:
    """Preveri, ali je besedilo veljaven OAuth Desktop client_secret JSON.

    Vrne (ok, sporočilo za stranko ob napaki).
    """
    try:
        data = json.loads(text)
    except ValueError:
        return False, "To ni veljavna JSON vsebina — kopiraj celotno vsebino datoteke."
    if not isinstance(data, dict):
        return False, "To ni veljavna JSON vsebina — kopiraj celotno vsebino datoteke."
    if isinstance(data.get("web"), dict):
        return False, (
            "Ta datoteka je za »Web application« — Granova potrebuje »Desktop app«.\n"
            "  V Cloud Console ustvari nove poverilnice tipa Desktop app."
        )
    installed = data.get("installed")
    if not (isinstance(installed, dict)
            and installed.get("client_id") and installed.get("client_secret")):
        return False, "V datoteki manjkajo OAuth podatki — je to res preneseni client_secret JSON?"
    return True, ""


def collect_pasted_json(first_line: str, read_line=input) -> str:
    """Ob prilepljenem večvrstičnem JSON bere vrstice, dokler se oklepaji ne zaprejo."""
    buf = first_line
    while buf.count("{") > buf.count("}"):
        try:
            buf += "\n" + read_line()
        except EOFError:
            break
    return buf


def downloads_candidates() -> list[Path]:
    """client_secret*.json v mapi Prenosi, najnovejša najprej (fizično ime je vedno Downloads)."""
    downloads = Path.home() / "Downloads"
    if not downloads.is_dir():
        return []
    return sorted(downloads.glob("client_secret*.json"),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def _save(text: str) -> None:
    CLIENT_SECRET_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLIENT_SECRET_PATH.write_text(text, encoding="utf-8")


def _read_entry(entry: str) -> tuple[str | None, str]:
    """Iz vnosa v terminal izlušči vsebino JSON datoteke.

    Vrne (vsebina ali None, sporočilo ob napaki). Prazen vnos pomeni
    »poišči v Prenosih«, pot pomeni povlečeno datoteko, `{` prilepljen JSON.
    """
    if not entry:
        found = downloads_candidates()
        if not found:
            return None, ("V mapi Prenosi ni datoteke client_secret*.json — "
                          "je prenos v koraku 4 končan?")
        path = found[0]
        answer = input(f"  Najdena datoteka {path.name} — jo uporabim? [D/n] ").strip().lower()
        if answer in {"n", "ne", "no"}:
            return None, "V redu — povleci pravo datoteko sem ali prilepi njeno vsebino."
        return path.read_text(encoding="utf-8"), ""

    if entry.lstrip().startswith("{"):
        return collect_pasted_json(entry), ""

    path = Path(entry.strip().strip('"').strip("'"))
    if path.is_file():
        return path.read_text(encoding="utf-8"), ""
    return None, (f"Datoteke ne najdem ({path}). Povleci jo v to okno, "
                  "prilepi njeno vsebino ali samo pritisni Enter.")


def run_wizard() -> bool:
    """Vodi stranko do shranjenega client_secret.json; vrne True ob uspehu."""
    total = len(STEPS) + 1
    print("→ Granova potrebuje enkratno dovoljenje tvojega Google računa.")
    print(f"  Vodila te bom skozi {total} kratkih korakov (~5 minut). Vsak korak")
    print("  sam odpre pravo stran v brskalniku — ti samo klikaš po navodilih.")
    print("  Če Google pokaže »Google hasn't verified this app«, je to pričakovano.")

    try:
        input("\n  Pritisni Enter za začetek ... ")
        for i, (title, text, urls) in enumerate(STEPS, 1):
            print(f"\nKorak {i}/{total} — {title}")
            for url in urls:
                webbrowser.open(url)
            print(f"  {text}")
            input("  Ko je narejeno, pritisni Enter ... ")

        print(f"\nKorak {total}/{total} — predaj datoteko Granovi")
        print("  Naredi eno od tega (kar ti je najlažje):")
        print("   • samo pritisni Enter — datoteko poiščem v mapi Prenosi,")
        print("   • ali povleci preneseno datoteko v to okno in pritisni Enter,")
        print("   • ali odpri datoteko, kopiraj vso vsebino in jo prilepi sem.")
        while True:
            entry = input("\n  Vnos: ").strip()
            text, message = _read_entry(entry)
            if text is None:
                print(f"  ✗ {message}")
                continue
            ok, message = validate_client_secret(text)
            if not ok:
                print(f"  ✗ {message}")
                continue
            _save(text)
            print(f"  ✓ Shranjeno v {CLIENT_SECRET_PATH}")
            return True
    except (EOFError, KeyboardInterrupt):
        print("\n  Nastavitev prekinjena.")
        return False
