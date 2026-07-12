# Granova — namestitev z enim ukazom (design)

Datum: 2026-07-12 · Status: predlog v pregledu

## Cilj

Nestrokovna stranka (macOS, brez VS Code in brez git znanja) prenese in nastavi
Granovo z **enim samim ukazom v terminalu**. Terminal jo vodi skozi vse korake.
Isti ukaz kasneje služi tudi za **posodobitev**. Enako na Windows.

## Potrjene odločitve

- Repozitorij `maticko911/Granova` je **javen** → `curl` do raw datotek deluje brez prijave.
- Predpogoje (Xcode ukazna orodja, Python, git) skript **sam zazna in vodi** namestitev.
- Prenos z `git clone` v fiksno mapo (`~/Granova` oz. `%USERPROFILE%\Granova`);
  ponovni zagon istega ukaza naredi `git pull` (posodobitve tečejo prek terminala).
- **Poverilnice ostanejo pri stranki**: vsaka si ustvari svoj OpenAI ključ in svoj
  Google Cloud projekt. V repozitoriju ni nobene skrivnosti (`.gitignore` že ščiti
  `.env`, `client_secret*.json`, `token.json`, `config.json`).
- Obe platformi: macOS (stranka) + Windows (razvoj, preverim v živo).

## Vstopna ukaza (gresta na vrh README in v NAVODILA.md)

macOS (Terminal):

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/maticko911/Granova/main/install.sh)"
```

Windows (PowerShell):

```
irm https://raw.githubusercontent.com/maticko911/Granova/main/install.ps1 | iex
```

Homebrew-vzorec `bash -c "$(curl …)"` namesto `curl | bash`, ker ohrani terminal
kot stdin — interaktivni pozivi (OpenAI ključ, Enter …) delujejo. Na Windows
`irm | iex` teče v trenutni seji, zato `Read-Host` prav tako deluje in datotečna
execution policy ne blokira ničesar.

## Komponente

### 1. `install.sh` (koren repozitorija; macOS bootstrap)

Koraki, vsak idempotenten:

1. **Xcode ukazna orodja** — `xcode-select -p`; če manjkajo, požene
   `xcode-select --install` (odpre sistemski dialog), izpiše »klikni Install in
   počakaj«, nato v zanki (vsakih 10 s) preverja `xcode-select -p`, dokler
   namestitev ni končana. Orodja prinesejo `git`, `python3` in `swiftc` naenkrat.
2. **Python ≥ 3.10** — preveri z `python3 -c "import sys; sys.exit(sys.version_info < (3,10))"`.
   CLT na starejših macOS prinese Python 3.9 → v tem primeru odpre
   https://www.python.org/downloads/ (`open`), izpiše navodilo »namesti in nato
   ponovno zaženi isti ukaz« in konča. (Brez Homebrew odvisnosti — YAGNI.)
3. **Clone/pull** — če `~/Granova/.git` ne obstaja: `git clone` (https URL).
   Sicer: `git -C ~/Granova pull --ff-only`; ob neuspehu (lokalne spremembe,
   divergenca) jasno navodilo: preimenuj mapo `Granova` in ponovi ukaz. Nikoli
   tihi `reset --hard`.
4. **Predaja** — `cd ~/Granova && /bin/bash setup.command`. Ker skript teče prek
   basha (ne z dvoklikom) in ker `git clone` ne nastavi quarantine atributa,
   **Gatekeeperjev »desni klik → Open« ples v celoti odpade**.
5. Kritični `read` pozivi v install.sh berejo iz `/dev/tty` (obramba, če kdo
   ukaz vseeno požene kot `curl | bash`).

### 2. `install.ps1` (koren repozitorija; Windows bootstrap)

1. **Python** — `where python` ni dovolj: Microsoft Store **stub** v
   `…\WindowsApps\python.exe` se pretvarja, da obstaja. Detekcija: požene
   `python --version`; če izhod prazen / koda 9009 / pot vsebuje `WindowsApps`,
   šteje kot »ni nameščen« → `winget install Python.Python.3.12`
   (z `--accept-source-agreements --accept-package-agreements`).
2. **git** — `git --version`; če manjka → `winget install Git.Git`.
3. **Osvežitev PATH** — po vsaki winget namestitvi trenutna seja PATH-a ne vidi:
   `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
   [Environment]::GetEnvironmentVariable('Path','User')`, nato ponovna preverba.
4. **winget manjka** (starejši Windows 10) — fallback: odpre python.org in
   git-scm.com v brskalniku, izpiše »namesti oboje in ponovno zaženi isti ukaz«, konča.
5. **Clone/pull** — kot na macOS, v `%USERPROFILE%\Granova`, `pull --ff-only`
   z istim navodilom ob neuspehu.
6. **Predaja** — `cmd /c "%USERPROFILE%\Granova\setup.bat"` (setup.bat si sam
   nastavi delovno mapo prek `%~dp0`).
7. **Brez šumnikov** v izpisih (kot setup.bat) — PowerShell 5.1 konzola sicer
   lahko popači UTF-8 znake.

### 3. `NAVODILA.md` (NOVO) — vodič za netehnično osebo

Napisan za nekoga, ki še nikoli ni odprl terminala. Vsebina:

1. **Kaj pripraviš prej (2 stvari)** — OpenAI ključ (povezava + »začne se s
   sk-«) in Google Cloud projekt s `client_secret.json` (povezava na
   SETUP_GOOGLE.md, korak za korakom).
2. **Kako odpreš terminal** — macOS: Cmd+Space → »Terminal« → Enter;
   Windows: Start → »PowerShell« → Enter.
3. **En ukaz** — kopiraj/prilepi blok za svojo platformo; opis, kaj se bo
   dogajalo (vprašanja v terminalu, Google prijava v brskalniku, macOS dialoga
   Screen Recording + Microphone).
4. **Kako veš, da deluje** — ikona Granove v sistemski vrstici / menijski vrstici;
   po prvem Meet klicu nov dokument v Drive mapi »Granola zapiski«.
5. **Posodobitev** — najprej zapri Granovo (ikona → Izhod), nato **isti ukaz**
   še enkrat; že narejeni koraki se preskočijo, app se znova zažene.
6. **Če kaj zaškripa** — kratka tabela simptom → rešitev (povzeto iz README).

### 4. Spremembe obstoječih datotek

- **README.md** — sekcija *Namestitev* se skrči na oba vstopna ukaza + povezavo
  na NAVODILA.md; ročna (git clone + dvoklik) pot ostane kot »za razvijalce«.
- **SETUP_GOOGLE.md** — `lozinsekmatic1@gmail.com` (dvakrat) zamenjan z »tvoj
  Gmail naslov« — dokument je zdaj namenjen strankam, ne le razvijalcu.
- `setup.command` / `setup.bat` — **brez sprememb** (že idempotentna); install
  skripta jima le predata štafeto.

## Robni primeri (iz battle-testa)

| # | Primer | Rešitev |
|---|---|---|
| 1 | CLT Python < 3.10 (macOS 12/13) | verzijska preverba + vodenje na python.org |
| 2 | MS Store python stub na Windows | detekcija stub-a, winget namestitev |
| 3 | PATH po winget namestitvi | osvežitev iz registra v isti seji |
| 4 | winget ni na voljo | brskalnik + »ponovi isti ukaz« |
| 5 | `git pull` konflikt | `--ff-only` + navodilo (preimenuj mapo), brez tihega brisanja |
| 6 | Granova že teče med posodobitvijo | single-instance varovalo prepreči podvojitev; NAVODILA: prej zapri prek ikone |
| 7 | Gatekeeper pri setup.command | odpade, ker install.sh skripto požene prek basha |

## Verifikacija

- **Windows (v živo, tukaj)**: `install.ps1` zagnan lokalno (najprej iz datoteke,
  nato prek `irm | iex` z GitHuba po pushu) na poti `%USERPROFILE%\Granova`;
  preverim clone, pull, predajo setup.bat, stub-detekcijo (simulirano).
- **macOS (stranka/prijatelj)**: en ukaz na svežem Macu; jaz zrcalim skript,
  logika pa je preverjena po delih (shellcheck + suhi tek s podtaknjenimi ukazi).
- **Testi**: install skripti sta bash/PS — brez pytest pokritja; obstoječih
  testov se ne dotikam.

## Izven obsega

- Homebrew, podpisan `.app` paket, samodejni »restart ob posodobitvi« prek
  socketa — kasnejši koraki.
- `granova/config.py` ostane nedotaknjen (lokalni popravek modela).
