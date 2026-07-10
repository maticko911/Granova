"""Ena vstopna točka: transkript (+ zapiski) -> MeetingResult ali None.

gate -> (stop, če zavrnjen) -> enhance -> content_generator -> sestavi rezultat
"""

import logging

from granova import content_generator, enhance, gate
from granova.models import MeetingResult

log = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7


def process_meeting(transcript: str, raw_notes: str = "") -> MeetingResult | None:
    verdict = gate.check(transcript)
    if not verdict.is_meaningful or verdict.confidence_score < CONFIDENCE_THRESHOLD:
        log.warning(
            "Pipeline: transkript zavrnjen (is_meaningful=%s, confidence=%.2f) — dokument ne bo ustvarjen",
            verdict.is_meaningful, verdict.confidence_score,
        )
        return None

    minutes = enhance.enhance(transcript, raw_notes)
    content = content_generator.generate(minutes)

    result = MeetingResult(
        notes=content["notes"],
        objava=content["objava"],
        enhanced_minutes=minutes,
        transcript=transcript,
    )
    log.info("Pipeline: končano — '%s'", result.notes.naslov)
    return result
