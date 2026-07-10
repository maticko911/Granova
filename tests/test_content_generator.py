from granova import content_generator
from granova.models import MeetingNotes, Objava


def test_generate_returns_notes_and_objava(mock_llm):
    result = content_generator.generate("UREJEN ZAPISNIK: kampanja, katalog, dogodek.")

    notes = result["notes"]
    objava = result["objava"]

    assert isinstance(notes, MeetingNotes)
    assert isinstance(objava, Objava)
    assert notes.povzetek
    assert notes.kljucne_tocke
    assert objava.besedilo
    # Dva strukturirana klica: zapiski + objava
    assert mock_llm["parse"] == ["MeetingNotes", "Objava"]
