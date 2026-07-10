import time

from granova.meet_detector import MeetDetector, find_meet_window


def test_active_call_detected_chrome():
    titles = ["Nekaj - Notepad", "Meet – abc-defg-hij - Google Chrome"]
    assert find_meet_window(titles) == "abc-defg-hij"


def test_named_meeting_detected():
    titles = ["Meet - Tedenski marketing - Google Chrome"]
    assert find_meet_window(titles) == "Tedenski marketing"


def test_home_tab_is_not_a_call():
    assert find_meet_window(["Google Meet - Google Chrome"]) is None
    assert find_meet_window(["Google Meet — Mozilla Firefox"]) is None


def test_no_windows():
    assert find_meet_window([]) is None
    assert find_meet_window(["Excel", "Spotify"]) is None


def test_detector_fires_started_and_ended():
    state = {"titles": []}
    events = []
    det = MeetDetector(
        on_call_started=lambda name: events.append(("started", name)),
        on_call_ended=lambda: events.append(("ended",)),
        poll_seconds=0.01,
        titles_fn=lambda: state["titles"],
        end_grace_polls=2,
    )
    det.start()
    time.sleep(0.05)
    assert events == []  # brez klica se nič ne zgodi

    state["titles"] = ["Meet – abc-defg-hij - Google Chrome"]
    time.sleep(0.05)
    assert ("started", "abc-defg-hij") in events

    # po dovolj zaporednih praznih ciklih se razglasi konec klica
    state["titles"] = []
    time.sleep(0.05)
    det.stop()
    assert events[-1] == ("ended",)
    assert events.count(("started", "abc-defg-hij")) == 1
