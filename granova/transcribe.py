"""Transkripcija enega avdio koščka v slovenščino.

Primarno `gpt-4o-transcribe`, ob napaki poskus ponovimo, nato pademo nazaj na
`whisper-1`. Vrne golo besedilo koščka.
"""
from __future__ import annotations

import io
import logging
import time

from granova.config import get_client

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "gpt-4o-transcribe"
FALLBACK_MODEL = "whisper-1"
LANGUAGE = "sl"


def _call(model: str, wav_bytes: bytes) -> str:
    response = get_client().audio.transcriptions.create(
        model=model,
        file=("chunk.wav", io.BytesIO(wav_bytes)),
        language=LANGUAGE,
    )
    return (response.text or "").strip()


def transcribe_chunk(wav_bytes: bytes) -> str:
    """Transkribira en WAV košček; ob vztrajni napaki vrne prazen niz (klic se ne sme sesuti)."""
    for attempt, model in enumerate([PRIMARY_MODEL, PRIMARY_MODEL, FALLBACK_MODEL]):
        try:
            return _call(model, wav_bytes)
        except Exception as exc:  # mrežne napake, rate limit, ...
            logger.warning("Transkripcija (%s, poskus %d) ni uspela: %s", model, attempt + 1, exc)
            time.sleep(min(2**attempt, 4))
    logger.error("Transkripcija koščka dokončno ni uspela — košček preskočen")
    return ""
