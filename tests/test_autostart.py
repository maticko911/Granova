from pathlib import Path, PurePosixPath

import pytest

from granova.autostart import (
    LAUNCHAGENT_LABEL,
    entry_path,
    launchagent_plist_content,
    windows_cmd_content,
)


def test_windows_entry_in_startup_folder(monkeypatch):
    monkeypatch.setenv("APPDATA", r"C:\Users\Test\AppData\Roaming")
    path = entry_path("win32")
    assert path.name == "Granova.cmd"
    assert path.parent == Path(
        r"C:\Users\Test\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
    )


def test_macos_entry_is_launchagent_plist():
    path = entry_path("darwin")
    assert path == Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHAGENT_LABEL}.plist"


def test_unsupported_platform_raises():
    with pytest.raises(NotImplementedError):
        entry_path("linux")


def test_windows_cmd_runs_pythonw_from_repo():
    content = windows_cmd_content(Path(r"C:\repo\Granola"))
    assert r'cd /d "C:\repo\Granola"' in content
    assert "pythonw" in content
    assert "app.py" in content


def test_launchagent_plist_has_label_and_app():
    content = launchagent_plist_content(PurePosixPath("/Users/test/Granola"))
    assert LAUNCHAGENT_LABEL in content
    assert "cd '/Users/test/Granola'" in content
    assert "app.py" in content
    assert "<key>RunAtLoad</key>" in content
