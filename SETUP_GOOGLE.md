# Granova — enkratna nastavitev Google računa

> **Tega dokumenta ti ni treba brati vnaprej:** `setup.bat` / `setup.command`
> te skozi vse spodnje korake vodi sam — v terminalu, korak za korakom, s
> samodejnim odpiranjem pravih strani. Preneseno JSON datoteko na koncu samo
> povlečeš v okno terminala (ali prilepiš njeno vsebino) in setup nadaljuje
> sam. Ta datoteka ostaja kot ročna referenca.

Da Granova po vsakem sestanku ustvari Google Doc (in vse dokumente zbira v eni
mapi »Granola zapiski« na Drive), potrebuje dovoljenje tvojega Google računa.
To narediš **enkrat**, traja ~5 minut. Edini ročni del je Google Cloud Console —
Google drugače ne dovoli namiznim aplikacijam dostopa do Docs/Drive/Calendar.

## 1. Ustvari projekt v Google Cloud Console

1. Odpri https://console.cloud.google.com in se prijavi z `lozinsekmatic1@gmail.com`.
2. Zgoraj levo klikni izbirnik projektov → **New project** → ime `Granova` → **Create**.
3. Počakaj, da se projekt ustvari, in ga izberi.

## 2. Vklopi tri API-je

Za vsakega: v iskalnik na vrhu vpiši ime → odpri → klikni **Enable**.

- **Google Docs API**
- **Google Drive API**
- **Google Calendar API**

## 3. Nastavi zaslon za soglasje (OAuth consent screen)

1. Meni ☰ → **APIs & Services** → **OAuth consent screen**.
2. Tip: **External** → **Create**.
3. Ime aplikacije: `Granova`; support e-pošta: tvoj naslov. Ostalo pusti prazno → shrani.
4. Pri korakih *Scopes* nič ne dodajaj (aplikacija jih zahteva sama) → naprej.
5. Pri **Test users** klikni **Add users** in dodaj `lozinsekmatic1@gmail.com` → shrani.

> Aplikacija ostane v načinu *Testing* — za osebno rabo je to dovolj in ne
> potrebuje Googlove verifikacije. Ob prvi prijavi bo Google pokazal opozorilo
> »Google hasn't verified this app« — to je pričakovano: klikni
> **Advanced → Go to Granova (unsafe) → Continue**.

## 4. Ustvari OAuth poverilnice (Desktop app)

1. **APIs & Services** → **Credentials** → **Create credentials** → **OAuth client ID**.
2. Application type: **Desktop app**, ime `Granova` → **Create**.
3. Klikni **Download JSON**.
4. Preneseno datoteko shrani kot `client_secret.json` v mapo `data/` **znotraj
   mape aplikacije** (npr. `Granova\data\client_secret.json`; če mape `data`
   ni, jo ustvari). Terminalski čarovnik ob nastavitvi to običajno stori
   samodejno — datoteko v Prenosih poišče in prekopira namesto tebe.

## 5. Zaženi nastavitev

Najlažje: dvoklikni `setup.bat` (Windows) oz. `setup.command` (macOS) — ta
poskrbi za vse korake naenkrat. Ročno v mapi projekta:

```
python -m granova.setup
```

(Samo Google del lahko poženeš tudi z `python -m granova.setup_google`.)

Odpre se brskalnik — prijavi se in dovoli dostop (glej opozorilo zgoraj).
Ukaz nato izpiše povezavo do skupne mape **Granola zapiski** in do
**preizkusnega dokumenta**. Odpri obe in preveri, da je dokument v mapi —
potem ga lahko izbrišeš.

Od tu naprej vse deluje samodejno: po vsakem Meet klicu se v mapi pojavi nov
dokument `«Ime sestanka» — YYYY-MM-DD` s povzetkom, objavo in celotnim transkriptom.

## Kaj Granova sme (in česa ne)

Zahtevani obsegi (`granova/auth.py`):

- `calendar.readonly` — samo branje koledarja (za ime sestanka),
- `documents` — ustvarjanje/pisanje Google Docs,
- `drive.file` — dostop **samo do datotek in map, ki jih ustvari Granova**;
  tvojih ostalih datotek na Drive aplikacija ne vidi.

Žeton se shrani v `token.json` v isti mapi kot `client_secret.json` in se osvežuje samodejno —
prijava v brskalniku je potrebna samo prvič.

## Nastavitve (neobvezno)

V `config.json` (v isti mapi kot `client_secret.json`):

- `docs_folder_name` — drugačno ime samodejne mape (privzeto `"Granola zapiski"`),
- `drive_folder_id` — id obstoječe mape, če želiš uporabiti točno določeno
  (sicer se mapa poišče/ustvari samodejno po imenu).
