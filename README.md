<div align="center">

# Granova

**Samodejni slovenski zapiski Google Meet klicev — lokalno, brez bota v klicu.**

Med klicem posname zvok, sproti izpisuje transkript, po koncu pa v Google Doc
zapiše povzetek, ključne točke, naloge in osnutek objave.

![Platforma](https://img.shields.io/badge/platforma-Windows%20%7C%20macOS%2013%2B-0A66C2)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)
![Zvok](https://img.shields.io/badge/zvok-obdelan%20lokalno-2E7D32)
![Jezik](https://img.shields.io/badge/jezik-sloven%C5%A1%C4%8Dina-8E44AD)

</div>

---

## Namestitev v treh ukazih

Predpogoj (enkrat): **Python 3.10+** ([python.org](https://www.python.org/downloads/) —
na Windows obkljukaj *Add Python to PATH*); na **Windows** še **Git**
([git-scm.com](https://git-scm.com/download/win)).

Odpri terminal — **macOS**: `Cmd + preslednica` → `Terminal` → Enter;
**Windows**: Start → `PowerShell` → Enter. Nato prilepi ukaze (po vsakem Enter):

**macOS**

```
git clone https://github.com/maticko911/Granova.git
cd Granova
bash setup.command
```

**Windows**

```
git clone https://github.com/maticko911/Granova.git
cd Granova
.\setup.bat
```

Od tu te setup sam vodi (OpenAI ključ → Google prijava → samodejni zagon).
Podrobnosti, predpogoji in posodobitev: [Namestitev](#namestitev).

---

## Kazalo

- [Zmožnosti](#zmožnosti)
- [Kako deluje](#kako-deluje)
- [Stanje po platformah](#stanje-po-platformah)
- [Namestitev](#namestitev)
- [Uporaba](#uporaba)
- [Tehnologija](#tehnologija)
- [Če kaj zaškripa](#če-kaj-zaškripa)
- [Varnost in zasebnost](#varnost-in-zasebnost)
- [Licenca](#licenca)

## Zmožnosti

- 🎙️ **Zajem zvoka brez bota** — sistemski zvok klica in mikrofon zajamem
  lokalno (Windows: WASAPI · macOS: ScreenCaptureKit).
- 🇸🇮 **Slovenski transkript** — prilagojen slovenščini (OpenAI).
- 📝 **Strukturiran zapisek** — povzetek, ključne točke, naloge in osnutek objave.
- 📄 **Naravnost v Google Docs** — vsak zapisek pristane v skupni Drive mapi.
- 🖥️ **Diskretno v ozadju** — ikona v sistemski vrstici in živo okno med klicem.
- 🔒 **Zasebno po zasnovi** — zvok se obdela lokalno, skrivnosti nikoli ne gredo v repozitorij.

## Kako deluje

```
1. Zazna klic     Granova opazi odprto okno Google Meet klica.
2. Posname zvok    Lokalno zajame zvok klica + moj mikrofon.
3. Transkribira    Sproti izpiše slovenski transkript v živo okno.
4. Povzame         Po koncu klica iz transkripta naredi strukturiran zapisek.
5. Shrani          Zapisek shrani kot nov Google Doc v mapo »Granola zapiski«.
```

## Stanje po platformah

Granovo razvijam in vsak dan uporabljam na **Windows**, kjer je v celoti
preverjena v živo. Dodal sem tudi **macOS** podporo — ista koda iz istega
repozitorija, ki se ob zagonu sama prilagodi sistemu.

| Zmožnost | Windows | macOS |
|---|:---:|:---:|
| Nastavitev, Google prijava, zapis v Docs | ✅ | ✅ |
| Sistemska vrstica + živo okno | ✅ | ✅ |
| Zajem zvoka + zaznava Meet klica | ✅ | ✅ *(macOS 13+)* |

> Na macOS uporabljam ScreenCaptureKit za sistemski zvok in Quartz za zaznavo
> Meet klica — enako obnašanje kot na Windows. Potrebuje macOS 13+ in enkratno
> namestitev Xcode ukaznih orodij (`xcode-select --install`), ki jo `setup.command`
> zahteva pri prevajanju pomočnika za zvok.

## Namestitev

### Kaj potrebujem (enkrat)

1. **Python 3.10+** — https://www.python.org/downloads/
   (na Windows med namestitvijo obkljukaj *Add Python to PATH*).
2. Na **Windows** še **Git** — https://git-scm.com/download/win
   (na macOS ni treba — sistem ga ponudi sam ob prvem `git` ukazu).
3. **OpenAI ključ** — https://platform.openai.com/api-keys (edini strošek).
4. **Google račun** + ~5 minut za Google Cloud Console — setup te skozi to
   vodi sam, korak za korakom (ročna referenca: [SETUP_GOOGLE.md](SETUP_GOOGLE.md)).

### Namestitev v treh ukazih

Odpri terminal — **macOS**: `Cmd + preslednica` → natipkaj `Terminal` → Enter;
**Windows**: Start → natipkaj `PowerShell` → Enter. Nato prilepi ukaze (po vsakem Enter):

**macOS**

```
git clone https://github.com/maticko911/Granova.git
cd Granova
bash setup.command
```

**Windows**

```
git clone https://github.com/maticko911/Granova.git
cd Granova
.\setup.bat
```

Od tu te setup sam vodi: vpraša za OpenAI ključ, te korak za korakom pelje
skozi Google Cloud Console (strani odpira sam, preneseno datoteko samo povlečeš
v terminal ali prilepiš njeno vsebino), odpre brskalnik za Google prijavo,
vklopi samodejni zagon ob prijavi in Granovo zažene v ozadju — ikona se pojavi
v sistemski/menijski vrstici.

> Na macOS te ob prvem snemanju vpraša za dovoljenji **Screen Recording** (za
> zvok klica in zaznavo Meet okna) in **Microphone** — potrdi ju. Če se snemanje
> po potrditvi še ne začne, enkrat zapri in znova zaženi Granovo (macOS pripne
> dovoljenje ob naslednjem zagonu).

### Posodobitev

Najprej zapri Granovo (ikona v vrstici → **Izhod**), nato v isti mapi:

```
cd Granova            # Windows: cd %USERPROFILE%\Granova
git pull
bash setup.command    # Windows: .\setup.bat
```

Že opravljeni koraki se preskočijo; Granova se znova zažene v ozadju.

## Uporaba

Ko je Granova enkrat nastavljena, teče tiho v sistemski vrstici in ne
potrebuje nobenega ročnega koraka — zažene se sama ob vsaki prijavi v
računalnik, ob vsakem Google Meet klicu začne snemati, ob koncu klica pa
sama zapiše zapisek. Terminala ni treba nikoli odpirati; `Start Granova`
skripti prideta prav le, če jo vmes ročno zaprem (v meniju ikone lahko
samodejni zagon tudi izklopim).

- **Zapiski**: Google Drive → mapa **Granola zapiski** (dokument
  `«Ime sestanka» — YYYY-MM-DD`).
- **Nastavitve in skrivnosti**: mapa `data/` **znotraj mape aplikacije**
  (`config.json`, `client_secret.json`, `token.json`). Ker živijo v mapi
  aplikacije, **izbris mape zbriše tudi vse skrivnosti** — ob ponovni uporabi je
  treba vnesti nov OpenAI ključ in znova odobriti Google. Mapa je v `.gitignore`
  in ne gre na GitHub.
- **Rezervni zapiski**, če Google ni na voljo: `data/notes` v isti mapi
  (Markdown; ob naslednjem zagonu se poskusi ponovno).

## Tehnologija

| Področje | Windows | macOS |
|---|---|---|
| Zajem zvoka | WASAPI (`pyaudiowpatch`) | ScreenCaptureKit (Swift pomočnik) |
| Zaznava klica | naslovi oken (`pygetwindow`) | Quartz `CGWindowList` |
| Transkripcija | OpenAI `gpt-4o-transcribe` (fallback `whisper-1`) | ↖ isto |
| Povzetek | OpenAI chat model, slovenski pozivi | ↖ isto |
| Shranjevanje | Google Docs + Drive API (obseg `drive.file`) | ↖ isto |
| Vmesnik | `pystray` (vrstica) + `tkinter` (živo okno) | ↖ isto |

Jedro (mešanje zvoka, transkripcija, povzetek, zapis) je platformno neodvisno;
razlikuje se le zajem zvoka in zaznava oken, ki se ob zagonu izbereta samodejno.

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

## Varnost in zasebnost

Skrivnosti (`client_secret.json`, `token.json`, `config.json`) živijo v mapi
`data/` **znotraj aplikacije** in so na disku **šifrirane** (glej
`granova/secrets_store.py`). Šifrirni ključ varuje operacijski sistem na
uporabnika — **Windows** DPAPI (`data/secret.key`, odklene ga samo tvoj Windows
račun na tem računalniku), **macOS** login Keychain. Za drugega uporabnika, za
kopijo mape ali za drug računalnik so datoteke neuporabne. Ker živijo v mapi
aplikacije, **izbris mape zbriše vse skrivnosti** — ob ponovni uporabi je treba
vnesti nov OpenAI ključ in znova odobriti Google. Mapa `data/` je v `.gitignore`
in nikoli ne gre v repozitorij.

Zvok se obdela lokalno; v klic ne vstopa noben bot. Aplikacija uporablja Google
obseg `drive.file` — vidi **samo** mape in dokumente, ki jih je sama ustvarila.

## Licenca

Osebni projekt brez formalne odprtokodne licence — koda je javno vidna zaradi
preglednosti, ni pa (še) namenjena za ponovno uporabo ali prispevke tretjih.
Če te kaj zanima ali najdeš hrošča, odpri Issue.

---

<div align="center">
<sub>Osebni projekt · slovenščina · brez strežnikov · samo OpenAI in Google API</sub>
</div>
