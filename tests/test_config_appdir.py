import sys
from pathlib import Path

from granova.config import _default_app_dir


def test_windows_uses_appdata(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", r"C:\Users\Test\AppData\Roaming")
    assert _default_app_dir() == Path(r"C:\Users\Test\AppData\Roaming") / "Granola"


def test_macos_uses_application_support(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    expected = Path.home() / "Library" / "Application Support" / "Granola"
    assert _default_app_dir() == expected


def test_linux_uses_xdg_config_home(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/home/test/.custom")
    assert _default_app_dir() == Path("/home/test/.custom") / "Granola"


def test_linux_falls_back_to_dot_config(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert _default_app_dir() == Path.home() / ".config" / "Granola"
