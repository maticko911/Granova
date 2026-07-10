"""Google Koledar — samo za obogatitev naslova dokumenta.

Sprožilec snemanja je zaznava Meet okna; koledar zgolj poišče trenutni dogodek
z Meet povezavo in njegov naslov uporabi kot naslov Google Doca. Če dogodka ni
(ad-hoc klic) ali koledar ni dosegljiv, se uporabi ime iz naslova okna.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from granova.config import get_setting

logger = logging.getLogger(__name__)

GRACE = timedelta(minutes=10)  # dogodek "velja" še malo pred začetkom in po koncu


def _parse(dt: str) -> datetime | None:
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def match_event_title(events: list[dict], now: datetime) -> str | None:
    """Čista funkcija: vrne naslov dogodka, ki poteka ob `now` in ima Meet povezavo.

    `events` so surovi dogodki iz Calendar API (start/end.dateTime, summary,
    hangoutLink/conferenceData). Prednost imajo dogodki z Meet povezavo.
    """
    candidates = []
    for ev in events:
        start = _parse(ev.get("start", {}).get("dateTime", ""))
        end = _parse(ev.get("end", {}).get("dateTime", ""))
        summary = (ev.get("summary") or "").strip()
        if not start or not end or not summary:
            continue
        if not (start - GRACE <= now <= end + GRACE):
            continue
        has_meet = bool(ev.get("hangoutLink") or ev.get("conferenceData"))
        candidates.append((has_meet, summary))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0], reverse=True)  # najprej tisti z Meet povezavo
    return candidates[0][1]


def fetch_current_event_title(creds, now: datetime | None = None) -> str | None:
    """Poišče naslov trenutnega dogodka; ob kakršnikoli napaki vrne None (nikoli ne blokira)."""
    try:
        from googleapiclient.discovery import build

        now = now or datetime.now(timezone.utc)
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        result = service.events().list(
            calendarId=get_setting("calendar_id", "primary"),
            timeMin=(now - timedelta(hours=2)).isoformat(),
            timeMax=(now + timedelta(hours=2)).isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        return match_event_title(result.get("items", []), now)
    except Exception:
        logger.exception("Branje koledarja ni uspelo — uporabim ime iz okna")
        return None
