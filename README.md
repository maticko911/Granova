# Granova

Lokalna namizna aplikacija, ki med **Google Meet** klicem sama posname zvok,
naredi **slovenski transkript** in po koncu klica v Google Doc zapiše
**povzetek, ključne točke, naloge in osnutek objave**. Vsi dokumenti se zbirajo
v eni Drive mapi **»Granola zapiski«**. Nič se ne pošilja na noben strežnik —
zvok se obdela lokalno, edini zunanji storitvi sta OpenAI API (transkripcija in
povzetek) in Google (shranjevanje dokumenta).

## Stanje po platformah

| | Windows | macOS |
|---|---|---|
| Nastavitev, Google prijava, zapis v Docs | ✅ | ✅ |
| Sistemska vrstica + živo okno | ✅ | ✅ |
| Zajem zvoka + zaznava Meet klica | ✅ | 🚧 naslednji mejnik |

**Windows deluje v celoti.** Na macOS enkratna nastavitev, Google integracija in
uporabniški vmesnik delujejo, zajem zvoka klica in samodejna zaznava Meet klica
pa še nista narejena (ScreenCaptureKit pomočnik je naslednji korak razvoja).

## Kaj potrebuješ (enkrat)

1. **Python 3.10+** — https://www.python.org/downloads/
   (na Windows pri namestitvi obkljukaj *Add Python to PATH*).
2. **OpenAI ključ** — https://platform.openai.com/api-keys (edini strošek).
3. **Google račun** + ~5 minut za Google Cloud Console — glej [SETUP_GOOGLE.md](SETUP_GOOGLE.md).

## Hitri začetek — Windows

1. Kloniraj / prenesi ta repozitorij.
2. Dvoklikni **`setup.bat`** — pripravi okolje, vpraša za OpenAI ključ,
   odpre brskalnik za Google prijavo in ponudi samodejni zagon ob prijavi.
3. Dvoklikni **`Start Granova.bat`** — ikona se pojavi v sistemski vrstici.

To je vse. Ob vsakem Meet klicu se pokaže živo okno s transkriptom; po koncu
klica se v Drive mapi »Granola zapiski« pojavi nov dokument.

## Hitri začetek — macOS

1. Kloniraj / prenesi ta repozitorij.
2. Desni klik na **`setup.command`** → **Open** (prvič macOS opozori, ker
   skripta ni podpisana) — enaki koraki kot na Windows.
3. Desni klik na **`Start Granova.command`** → **Open**.

> macOS bo ob prvem snemanju (ko bo zajem zvoka narejen) vprašal za dovoljenji
> *Microphone* in *Screen Recording* — to je pričakovano.

## Kje je kaj

- **Zapiski**: Google Drive → mapa **Granola zapiski** (dokument
  `«Ime sestanka» — YYYY-MM-DD`).
- **Nastavitve in skrivnosti** (izven repozitorija, ne gredo na GitHub):
  - Windows: `%APPDATA%\Granola` (`config.json`, `client_secret.json`, `token.json`)
  - macOS: `~/Library/Application Support/Granola`
- **Rezervni zapiski**, če Google ni na voljo: `Granola/notes` v isti mapi
  (Markdown; ob naslednjem zagonu se poskusi ponovno).

## Odpravljanje težav

- **`pip` javi SSL napako** — nekatera omrežja prestrezajo SSL; `setup` skripta
  samodejno ponovi z `--trusted-host pypi.org --trusted-host files.pythonhosted.org`.
- **»Google hasn't verified this app«** pri prijavi — pričakovano (aplikacija je
  v načinu *Testing*): **Advanced → Go to Granova (unsafe) → Continue**.
- **Ni zvoka / napaka pri snemanju na macOS** — zajem zvoka na macOS še ni
  narejen (glej tabelo zgoraj); to ni napaka v nastavitvi.
- **Kaj se dogaja?** — zaženi `Start Granova (debug).bat` (Windows), da vidiš
  dnevnik v konzoli.

## Ročni ukazi (če jih raje tipkaš)

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt   # macOS: .venv/bin/python3
python -m granova.setup        # celotna enkratna nastavitev
python app.py                  # zagon aplikacije
python -m pytest tests/ -q     # testi
```

## Varnost

Skrivnosti (`.env`, `client_secret*.json`, `token.json`, `config.json`) so v
`.gitignore` in nikoli ne smejo v repozitorij. Aplikacija uporablja Google obseg
`drive.file` — vidi **samo** mape in dokumente, ki jih je sama ustvarila.
