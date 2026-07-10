"""Zaznava aktivnega Google Meet klica prek naslovov oken.

Med klicem ima zavihek naslov "Meet – abc-defg-hij" (ali ime sestanka), brskalnik
pa to prenese v naslov okna (npr. "Meet – abc-defg-hij - Google Chrome").
Domača stran je "Google Meet" in se NE šteje za klic.

`find_meet_window` je čista funkcija (testabilna brez oken); `MeetDetector`
periodično bere naslove vseh oken in sproži call-started / call-ended.
"""
from __future__ import annotations

import logging
import re
import threading

logger = logging.getLogger(__name__)

# "Meet – X" / "Meet - X" / "Meet — X", a ne "Google Meet" (domača stran)
_MEET_RE = re.compile(r"(?<!Google )\bMeet [–—-] (\S.*)")

POLL_SECONDS = 3.0
END_GRACE_POLLS = 2  # toliko zaporednih praznih ciklov, preden razglasimo konec


def find_meet_window(titles: list[str]) -> str | None:
    """Vrne ime sestanka iz naslova okna z aktivnim Meet klicem, sicer None."""
    for title in titles:
        m = _MEET_RE.search(title or "")
        if m:
            name = m.group(1)
            # odreži pripono brskalnika ("... - Google Chrome" ipd.)
            name = re.split(r" [-–—] (?:Google Chrome|Microsoft.*Edge|Mozilla Firefox|Brave|Opera|Chromium)", name)[0]
            return name.strip()
    return None


class MeetDetector:
    """Vsakih nekaj sekund preveri okna; javi začetek in konec Meet klica."""

    def __init__(
        self,
        on_call_started,
        on_call_ended,
        poll_seconds: float = POLL_SECONDS,
        titles_fn=None,
        end_grace_polls: int = END_GRACE_POLLS,
    ) -> None:
        if titles_fn is None:
            import pygetwindow

            titles_fn = pygetwindow.getAllTitles
        self._titles_fn = titles_fn
        self._on_started = on_call_started
        self._on_ended = on_call_ended
        self._poll_seconds = poll_seconds
        self._end_grace_polls = end_grace_polls
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._poll_seconds + 2)

    def _loop(self) -> None:
        in_call = False
        misses = 0
        while not self._stop_event.wait(self._poll_seconds):
            try:
                name = find_meet_window(list(self._titles_fn()))
            except Exception:
                logger.exception("Branje naslovov oken ni uspelo")
                continue
            if name:
                misses = 0
                if not in_call:
                    in_call = True
                    logger.info("Meet klic zaznan: %s", name)
                    self._on_started(name)
            elif in_call:
                misses += 1
                if misses >= self._end_grace_polls:
                    in_call = False
                    misses = 0
                    logger.info("Meet klic končan")
                    self._on_ended()
