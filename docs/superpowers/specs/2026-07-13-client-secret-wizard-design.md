# Terminalski čarovnik za client_secret.json — zasnova

**Datum:** 2026-07-13
**Status:** potrjeno (ustno, v pogovoru)

## Problem

Ob prvem zagonu `python -m granova.setup` (prek `setup.bat` / `setup.command`)
se ob manjkajočem `client_secret.json` izpiše le napaka s sklicem na
SETUP_GOOGLE.md in ukaz za ponovni zagon. Stranka je netehnična, nima VS Code
in ne bo brala markdown datotek — nastavitev se tu ustavi.

## Cilj

Setup stranko **sam vodi** skozi Google Cloud Console in **sam dokonča**
namestitev, ko stranka datoteko preda v terminal. Nič več »ponovno zaženi ukaz«.

## Rešitev

Nov modul `granova/client_secret_wizard.py` s funkcijo `run_wizard() -> bool`,
ki jo `run_google_setup()` pokliče namesto izpisa napake.

### 1. Vodeni koraki v terminalu

Koraki iz SETUP_GOOGLE.md, prevedeni v interaktivno obliko — vsak korak:

1. izpiše kratka navodila (kaj klikniti),
2. sam odpre pravo stran v brskalniku (globoke povezave v Cloud Console),
3. počaka na Enter, preden nadaljuje.

Koraki: nov projekt → vklop treh API-jev (Docs, Drive, Calendar) → OAuth
consent screen (External, test user = strankin e-naslov) → OAuth client ID
(Desktop app) + Download JSON.

### 2. Sprejem datoteke (trije načini, en poziv)

Zanka na koncu čarovnika sprejme karkoli od tega:

- **prazen Enter** — čarovnik sam poišče `client_secret*.json` v mapi
  `~/Downloads` (najnovejšo) in vpraša »jo uporabim? [D/n]«,
- **povlečeno datoteko** — terminal prilepi pot (z ali brez narekovajev),
- **prilepljeno vsebino** — vrstica, ki se začne z `{`; večvrstični JSON se
  bere naprej, dokler se oklepaji ne zaprejo.

### 3. Validacija in shranjevanje

- JSON mora imeti ključ `installed` s `client_id` in `client_secret`.
- Ključ `web` namesto `installed` → prijazno sporočilo, da je bila izbrana
  napačna vrsta (Web application namesto Desktop app), in nov poskus.
- Veljavna vsebina se zapiše v `APP_DIR/client_secret.json`, čarovnik vrne
  `True` in `run_google_setup()` **takoj nadaljuje** (prijava v brskalniku,
  preizkusni dokument, zagon v ozadju).

### Prekinitev

Ctrl+C ali EOF (neinteraktivni stdin) → `False`; kličoča koda izpiše, s
katerim ukazom se nastavitev nadaljuje, in sklic na SETUP_GOOGLE.md kot
ročno alternativo.

## Zunaj obsega

- Spletni vmesnik za nalaganje datoteke (preveč kode za korist).
- Samodejno ustvarjanje Cloud projekta prek API-ja (Google tega namiznim
  aplikacijam ne omogoča brez obstoječih poverilnic).

## Prizadete datoteke

- `granova/client_secret_wizard.py` (novo),
- `granova/setup_google.py` (klic čarovnika namesto napake),
- `SETUP_GOOGLE.md` (opomba, da setup vodi sam; datoteka ostane kot referenca).
