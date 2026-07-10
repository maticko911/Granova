"""GATE vzorec: ali je transkript sploh smiseln sestanek?

Prazni, prekratki ali popačeni transkripti ne smejo proizvesti dokumenta.
"""

import logging

from granova import llm
from granova.models import MeetingGate

log = logging.getLogger(__name__)

# Pod to dolžino ne trošimo API klica — očitno ni pravega sestanka.
MIN_TRANSCRIPT_CHARS = 50

SYSTEM_PROMPT = """Si strog ocenjevalec transkriptov sestankov v slovenščini.
Oceni, ali podani transkript vsebuje smiseln poslovni pogovor, iz katerega se
da narediti zapiske (teme, odločitve, naloge).

Transkript NI smiseln, če je: prazen ali skoraj prazen, popačen/nerazumljiv,
samo tehnično preverjanje zvoka ("me slišite?"), ali nepovezano besedilo brez vsebine.
Vrni is_meaningful in confidence_score (0-1)."""


def check(transcript: str) -> MeetingGate:
    if len(transcript.strip()) < MIN_TRANSCRIPT_CHARS:
        log.info("Gate: transkript prekratek (%d znakov), zavrnjen brez API klica", len(transcript.strip()))
        return MeetingGate(is_meaningful=False, confidence_score=1.0)

    result = llm.parse(SYSTEM_PROMPT, transcript, MeetingGate)
    log.info("Gate: is_meaningful=%s, confidence=%.2f", result.is_meaningful, result.confidence_score)
    return result
