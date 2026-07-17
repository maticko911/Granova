"""Zaznava aktivnega Google Meet klica prek naslovov zavihkov / oken.

Med klicem ima zavihek naslov "Meet – abc-defg-hij" (ali ime sestanka).
Domača stran je "Google Meet" in se NE šteje za klic.

Kje beremo naslove:
  * Windows: naslovi oken prek pygetwindow.
  * macOS:   naslovi zavihkov brskalnikov prek AppleScript (Automation) — macOS
    za to sam vpraša »… wants to control …«, kar je dovolj. Branje naslovov OKEN
    prek Quartza namreč zahteva dovoljenje Screen Recording in brez njega tiho
    vrne prazna imena (zaznava tedaj nikoli ne steče); Quartz ostane le rezerva.

`find_meet_window` je čista funkcija (testabilna brez oken); `MeetDetector`
periodično bere naslove in sproži call-started / call-ended.
"""
from __future__ import annotations

import logging
import re
import subprocess
import threading

logger = logging.getLogger(__name__)

# "Meet – X" / "Meet - X" / "Meet — X", a ne "Google Meet" (domača stran)
_MEET_RE = re.compile(r"(?<!Google )\bMeet [–—-] (\S.*)")

POLL_SECONDS = 3.0
END_GRACE_POLLS = 2  # toliko zaporednih praznih ciklov, preden razglasimo konec


def default_titles_fn():
    """Vrne funkcijo za branje naslovov vseh oken na trenutni platformi."""
    import sys

    if sys.platform == "win32":
        import pygetwindow

        return pygetwindow.getAllTitles
    if sys.platform == "darwin":
        return _mac_window_titles
    raise NotImplementedError(f"Branje naslovov oken za {sys.platform} še ni podprto")


# Brskalniki, ki znajo prek AppleScript vrniti naslove svojih zavihkov.
# Ključ je bundle ID (za preverjanje, ali teče), vrednost ime aplikacije za "tell".
_SCRIPTABLE_BROWSERS = {
    "com.google.Chrome": "Google Chrome",
    "com.google.Chrome.canary": "Google Chrome Canary",
    "com.microsoft.edgemac": "Microsoft Edge",
    "com.brave.Browser": "Brave Browser",
    "org.chromium.Chromium": "Chromium",
    "company.thebrowser.Browser": "Arc",
    "com.vivaldi.Vivaldi": "Vivaldi",
    "com.operasoftware.Opera": "Opera",
    "com.apple.Safari": "Safari",
}


def _mac_running_browsers() -> list[str]:
    """Imena scriptabilnih brskalnikov, ki trenutno tečejo (brez zaganjanja).

    Preverimo prek NSWorkspace (ne potrebuje dovoljenj), da z AppleScript ne
    zaženemo brskalnika, ki sploh ni odprt.
    """
    try:
        from AppKit import NSWorkspace
    except Exception:
        logger.debug("AppKit ni na voljo — preskočim branje zavihkov", exc_info=True)
        return []
    running = {
        app.bundleIdentifier()
        for app in NSWorkspace.sharedWorkspace().runningApplications()
        if app.bundleIdentifier()
    }
    return [name for bid, name in _SCRIPTABLE_BROWSERS.items() if bid in running]


def _browser_tab_script(app_name: str) -> str:
    """AppleScript, ki vrne naslove vseh zavihkov danega brskalnika (po vrsticah)."""
    prop = "name" if app_name == "Safari" else "title"  # Safari: name, Chromium: title
    return (
        f'tell application "{app_name}"\n'
        '\tset out to ""\n'
        "\trepeat with w in windows\n"
        "\t\trepeat with t in tabs of w\n"
        f"\t\t\tset out to out & ({prop} of t) & linefeed\n"
        "\t\tend repeat\n"
        "\tend repeat\n"
        "\treturn out\n"
        "end tell"
    )


def _mac_browser_tab_titles() -> list[str]:
    """Naslovi vseh zavihkov odprtih brskalnikov prek AppleScript (Automation).

    Zajame tudi zavihke v ozadju in NE potrebuje dovoljenja Screen Recording.
    Ob prvem klicu macOS vpraša »… wants to control …«; po potrditvi deluje tiho,
    tudi pri samodejnem zagonu. Če je dovoljenje zavrnjeno, osascript vrne napako
    in ta brskalnik le preskočimo (brez izjeme, brez ponavljajočega dnevnika).
    """
    titles: list[str] = []
    for name in _mac_running_browsers():
        try:
            res = subprocess.run(
                ["osascript", "-e", _browser_tab_script(name)],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if res.returncode == 0:
            titles.extend(line for line in res.stdout.splitlines() if line.strip())
    return titles


def _quartz_window_titles() -> list[str]:
    """Naslovi vidnih oken prek Quartz — zahteva dovoljenje Screen Recording.

    Brez tega dovoljenja so imena oken prazna, zato to ni glavna pot, le rezerva
    (npr. za brskalnike brez AppleScripta, ki pa imajo Screen Recording dodeljen).
    """
    import Quartz

    info = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    return [w.get(Quartz.kCGWindowName, "") for w in (info or [])]


def _mac_window_titles() -> list[str]:
    """Naslovi za zaznavo Meeta na macOS: zavihki brskalnikov + rezervni Quartz."""
    titles = _mac_browser_tab_titles()
    try:
        titles.extend(_quartz_window_titles())
    except Exception:
        logger.debug("Quartz branje oken ni uspelo", exc_info=True)
    return titles


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
            titles_fn = default_titles_fn()
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
