from granova import llm, pipeline
from granova.models import MeetingGate, MeetingResult
from tests.conftest import SAMPLE_TRANSCRIPT


def test_end_to_end_success(mock_llm):
    result = pipeline.process_meeting(SAMPLE_TRANSCRIPT, raw_notes="pomembno: potrditi katalog")

    assert isinstance(result, MeetingResult)
    assert result.notes.naslov == "Marketinški sestanek"
    assert result.objava.besedilo
    assert result.transcript == SAMPLE_TRANSCRIPT
    assert result.enhanced_minutes.startswith("UREJEN ZAPISNIK")
    # gate -> notes -> objava
    assert mock_llm["parse"] == ["MeetingGate", "MeetingNotes", "Objava"]
    # Uporabnikovi zapiski so prišli v enhance korak
    assert "pomembno: potrditi katalog" in mock_llm["complete"][0]


def test_rejected_transcript_returns_none(mock_llm):
    result = pipeline.process_meeting("kratko")
    assert result is None
    # Gate je zavrnil lokalno (prekratek) — noben LLM klic ni bil narejen
    assert mock_llm["parse"] == []
    assert mock_llm["complete"] == []


def test_low_confidence_returns_none(monkeypatch, mock_llm):
    monkeypatch.setattr(
        llm, "parse",
        lambda system, user, schema, model=None: MeetingGate(is_meaningful=True, confidence_score=0.4),
    )
    result = pipeline.process_meeting(SAMPLE_TRANSCRIPT)
    assert result is None
    assert mock_llm["complete"] == []
