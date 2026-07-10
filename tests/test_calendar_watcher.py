from datetime import datetime, timezone

from granova.calendar_watcher import match_event_title

NOW = datetime(2026, 7, 9, 10, 30, tzinfo=timezone.utc)


def ev(summary, start, end, meet=True):
    e = {
        "summary": summary,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }
    if meet:
        e["hangoutLink"] = "https://meet.google.com/abc-defg-hij"
    return e


def test_current_event_matched():
    events = [ev("Tedenski marketing", "2026-07-09T10:00:00Z", "2026-07-09T11:00:00Z")]
    assert match_event_title(events, NOW) == "Tedenski marketing"


def test_past_and_future_events_ignored():
    events = [
        ev("Jutranji standup", "2026-07-09T08:00:00Z", "2026-07-09T08:15:00Z"),
        ev("Popoldanski pregled", "2026-07-09T15:00:00Z", "2026-07-09T16:00:00Z"),
    ]
    assert match_event_title(events, NOW) is None


def test_event_with_meet_link_preferred():
    events = [
        ev("Fokus blok", "2026-07-09T10:00:00Z", "2026-07-09T11:00:00Z", meet=False),
        ev("Klic s stranko", "2026-07-09T10:00:00Z", "2026-07-09T11:00:00Z", meet=True),
    ]
    assert match_event_title(events, NOW) == "Klic s stranko"


def test_grace_period_before_start():
    # klic se pridruži 5 min pred uradnim začetkom
    events = [ev("Sestanek", "2026-07-09T10:35:00Z", "2026-07-09T11:00:00Z")]
    assert match_event_title(events, NOW) == "Sestanek"


def test_all_day_or_malformed_events_skipped():
    events = [
        {"summary": "Dopust", "start": {"date": "2026-07-09"}, "end": {"date": "2026-07-10"}},
        {"summary": ""},
    ]
    assert match_event_title(events, NOW) is None
