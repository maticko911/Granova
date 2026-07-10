from granova import gate, llm
from granova.models import MeetingGate
from tests.conftest import SAMPLE_TRANSCRIPT


def test_short_transcript_rejected_without_api_call(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("Za prekratek transkript se API ne sme klicati")

    monkeypatch.setattr(llm, "parse", boom)

    result = gate.check("me slišite?")
    assert result.is_meaningful is False
    assert result.confidence_score == 1.0


def test_meaningful_transcript_passes(mock_llm):
    result = gate.check(SAMPLE_TRANSCRIPT)
    assert result.is_meaningful is True
    assert mock_llm["parse"] == ["MeetingGate"]


def test_garbled_transcript_rejected(monkeypatch):
    monkeypatch.setattr(
        llm, "parse",
        lambda system, user, schema, model=None: MeetingGate(is_meaningful=False, confidence_score=0.9),
    )
    result = gate.check("x " * 100)
    assert result.is_meaningful is False
