# Granova

Granovo sem naredil zase, da mi med **Google Meet** klici ni treba ročno pisati
zapiskov. Aplikacija med klicem sama posname zvok, naredi **slovenski
transkript** in po koncu klica v Google Doc zapiše **povzetek, ključne točke,
naloge in osnutek objave**. Vse svoje zapiske zbiram v eni Drive mapi
**»Granola zapiski«**.

Vse teče lokalno na mojem računalniku — nič ne pošiljam na noben svoj strežnik.
Edini zunanji storitvi, ki ju uporabljam, sta **OpenAI API** (transkripcija in
povzetek; edini strošek) in **Google** (shranjevanje končnega dokumenta).

## Stanje po platformah

Granovo razvijam in vsak dan uporabljam na **Windows**, kjer je v celoti
preverjena v živo. Dodal sem tudi **macOS** podporo (isti repozitorij, ista
koda — ob zagonu se sama prilagodi sistemu), da jo lahko poganjam tudi na Macu.

| | Windows | macOS |
|---|---|---|
| Nastavitev, Google prijava, zapis v Docs | ✅ | ✅ |
| Sistemska vrstica + živo okno | ✅ | ✅ |
| Zajem zvoka + zaznava Meet klica | ✅ | ✅ (macOS 13+) |

Na macOS uporabljam ScreenCaptureKit za sistemski zvok in Quartz za zaznavo Meet
klica — enako obnašanje kot na Windows. Potrebuje macOS 13 ali novejši ter
enkratno namestitev Xcode ukaznih orodij (`xcode-select --install`), ki jo
`setup.command` zahteva pri prevajanju pomočnika za zvok.

## Kaj potrebujem (enkrat)

1. **Python 3.10+** — https://www.python.org/downloads/
   (na Windows pri namestitvi obkljukam *Add Python to PATH*).
2. **OpenAI ključ** — https://platform.openai.com/api-keys (edini strošek).
3. **Google račun** + ~5 minut za Google Cloud Console — glej [SETUP_GOOGLE.md](SETUP_GOOGLE.md).

## Kako zaženem — Windows

1. Kloniram / prenesem ta repozitorij.
2. Dvokliknem **`setup.bat`** — pripravi okolje, vpraša za OpenAI ključ,
   odpre brskalnik za Google prijavo in ponudi samodejni zagon ob prijavi.
3. Dvokliknem **`Start Granova.bat`** — ikona se pojavi v sistemski vrstici.

To je vse. Ob vsakem Meet klicu se mi pokaže živo okno s transkriptom; po koncu
klica se v Drive mapi »Granola zapiski« pojavi nov dokument.

## Kako zaženem — macOS

1. Kloniram / prenesem ta repozitorij.
2. Desni klik na **`setup.command`** → **Open** (prvič macOS opozori, ker
   skripta ni podpisana) — enaki koraki kot na Windows.
3. Desni klik na **`Start Granova.command`** → **Open**.

> macOS me ob prvem snemanju vpraša za dovoljenji **Screen Recording** (za
> zvok klica in zaznavo Meet okna) in **Microphone** — potrdim ju. Če se
> snemanje po potrditvi še ne začne, enkrat zaprem in znova zaženem Granovo
> (macOS pripne dovoljenje ob naslednjem zagonu).

## Kje je kaj

- **Zapiski**: Google Drive → mapa **Granola zapiski** (dokument
  `«Ime sestanka» — YYYY-MM-DD`).
- **Nastavitve in skrivnosti** (izven repozitorija, ne gredo na GitHub):
  - Windows: `%APPDATA%\Granola` (`config.json`, `client_secret.json`, `token.json`)
  - macOS: `~/Library/Application Support/Granola`
- **Rezervni zapiski**, če Google ni na voljo: `Granola/notes` v isti mapi
  (Markdown; ob naslednjem zagonu se poskusi ponovno).

## Če kaj zaškripa

- **`pip` javi SSL napako** — nekatera omrežja prestrezajo SSL; `setup` skripta
  samodejno ponovi z `--trusted-host pypi.org --trusted-host files.pythonhosted.org`.
- **»Google hasn't verified this app«** pri prijavi — pričakovano (aplikacija je
  v načinu *Testing*): **Advanced → Go to Granova (unsafe) → Continue**.
- **Ni zvoka / napaka pri snemanju na macOS** — preverim, da sta v *System
  Settings → Privacy & Security* potrjeni dovoljenji **Screen Recording** in
  **Microphone** za Terminal (oz. program, ki zažene Granovo), nato Granovo
  znova zaženem. Če `setup.command` javi, da manjka `swiftc`, najprej zaženem
  `xcode-select --install`.
- **Kaj se dogaja?** — zaženem `Start Granova (debug).bat` (Windows), da vidim
  dnevnik v konzoli.

## Ročni ukazi (če jih raje tipkam)

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt   # macOS: .venv/bin/python3
python -m granova.setup        # celotna enkratna nastavitev
python app.py                  # zagon aplikacije
```

## Varnost

Skrivnosti (`.env`, `client_secret*.json`, `token.json`, `config.json`) so v
`.gitignore` in nikoli ne gredo v repozitorij. Aplikacija uporablja Google obseg
`drive.file` — vidi **samo** mape in dokumente, ki jih je sama ustvarila.
