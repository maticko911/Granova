"""Skupni mocki: nadomestimo granova.llm.complete/parse, da testi ne kličejo OpenAI."""

import pytest

from granova import llm
from granova.models import MeetingGate, MeetingNotes, Objava

SAMPLE_TRANSCRIPT = (
    "Dobro jutro vsem. Danes se dogovorimo za jesensko kampanjo. "
    "Marko pripravi plan objav do 25. julija, Nina uredi fotografije do konca julija. "
    "Potrdili smo 700 izvodov kataloga. Dogodek za stranke bo 15. oktobra."
)

FAKE_NOTES = MeetingNotes(
    naslov="Marketinški sestanek",
    povzetek="Ekipa je uskladila jesensko kampanjo, katalog in dogodek za stranke.",
    kljucne_tocke=["Jesenska kampanja 60/40 v korist Instagrama", "Katalog v 700 izvodih"],
    odlocitve=["Potrjenih 700 izvodov kataloga"],
    naloge=[],
    udelezenci=["Marko", "Nina"],
)

FAKE_OBJAVA = Objava(
    besedilo="Pripravljamo nekaj posebnega za jesen! Spremljajte nas.",
    predlogi=["#jesen2026", "CTA: prijavite se na dogodek"],
)


@pytest.fixture
def mock_llm(monkeypatch):
    """llm.parse vrača smiselne fake modele glede na zahtevano shemo, llm.complete fiksen zapisnik.

    Vrne dict s seznamom klicev za asercije.
    """
    calls = {"parse": [], "complete": []}

    def fake_parse(system, user, schema, model=None):
        calls["parse"].append(schema.__name__)
        if schema is MeetingGate:
            return MeetingGate(is_meaningful=True, confidence_score=0.95)
        if schema is MeetingNotes:
            return FAKE_NOTES
        if schema is Objava:
            return FAKE_OBJAVA
        raise AssertionError(f"Nepričakovana shema: {schema}")

    def fake_complete(system, user, model=None):
        calls["complete"].append(user)
        return "UREJEN ZAPISNIK: kampanja, katalog, dogodek."

    monkeypatch.setattr(llm, "parse", fake_parse)
    monkeypatch.setattr(llm, "complete", fake_complete)
    return calls
