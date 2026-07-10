"""Sejna zanka snemanja: zajem → mix → transkripcija → sprotno besedilo.

Vsakih ~15 s vzame nabrani zvok, ga zmeša v mono 16 kHz WAV in transkribira.
Besedilo koščka gre prek `on_chunk` callbacka v živo okno IN se pripenja v
končni transkript (ena sama transkripcija — koščki SO končni transkript).
Zajem medtem teče naprej v ozadju, zato se nič ne izgubi.
"""
from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)

SEGMENT_SECONDS = 15.0
SILENCE_TIMEOUT_SECONDS = 300.0  # 5 min tišine -> varovalka samodejno ustavi


class Recorder:
    """Snema eno sejo (en klic) in sproti gradi transkript.

    Odvisnosti so injicirane zaradi testov; privzeto se uporabijo prave
    (WASAPI zajem, numpy mix, OpenAI transkripcija).
    """

    def __init__(
        self,
        capture=None,
        transcribe_fn=None,
        mix_fn=None,
        silence_fn=None,
        on_chunk=None,
        on_silence_timeout=None,
        segment_seconds: float = SEGMENT_SECONDS,
        silence_timeout_seconds: float = SILENCE_TIMEOUT_SECONDS,
    ) -> None:
        if capture is None:
            from granova.audio_capture import get_capture

            capture = get_capture()
        if transcribe_fn is None:
            from granova.transcribe import transcribe_chunk

            transcribe_fn = transcribe_chunk
        if mix_fn is None or silence_fn is None:
            from granova import audio_pipeline

            mix_fn = mix_fn or audio_pipeline.mix_to_wav
            silence_fn = silence_fn or audio_pipeline.is_silent

        self._capture = capture
        self._transcribe = transcribe_fn
        self._mix = mix_fn
        self._is_silent = silence_fn
        self._on_chunk = on_chunk
        self._on_silence_timeout = on_silence_timeout
        self._segment_seconds = segment_seconds
        self._silence_timeout = silence_timeout_seconds

        self._chunks: list[str] = []
        self._silence_elapsed = 0.0
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def transcript(self) -> str:
        return " ".join(c for c in self._chunks if c)

    def start(self) -> None:
        self._stop_event.clear()
        self._capture.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> str:
        """Ustavi snemanje, obdela še zadnji delni košček in vrne celoten transkript."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._segment_seconds + 30)
        self._process_segment()  # še kar je ostalo v medpomnilniku
        self._capture.stop()
        return self.transcript

    def _loop(self) -> None:
        while not self._stop_event.wait(self._segment_seconds):
            self._process_segment()

    def _process_segment(self) -> None:
        try:
            system, mic = self._capture.drain()
            wav = self._mix(system, mic)
            if self._is_silent(wav):
                self._silence_elapsed += self._segment_seconds
                if self._silence_elapsed >= self._silence_timeout and self._on_silence_timeout:
                    logger.info("Varovalka: %.0f s tišine — sprožam samodejno ustavitev", self._silence_elapsed)
                    self._on_silence_timeout()
                return
            self._silence_elapsed = 0.0
            text = self._transcribe(wav)
            if text:
                self._chunks.append(text)
                if self._on_chunk:
                    self._on_chunk(text)
        except Exception:
            logger.exception("Napaka pri obdelavi koščka — snemanje se nadaljuje")
