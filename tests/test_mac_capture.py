"""Testi macOS zajema in izbire platforme — brez naprav, tečejo tudi na Windows."""
import io
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from granova.audio_capture import get_capture
from granova.audio_capture.mac_capture import MacCapture, _ByteBuffer
from granova.meet_detector import _mac_window_titles, default_titles_fn


# ---------- _ByteBuffer ----------

def test_byte_buffer_drain_returns_pcm_and_empties():
    buf = _ByteBuffer(rate=48000, channels=1)
    buf.append(b"ab")
    buf.append(b"cd")
    pcm = buf.drain()
    assert pcm.data == b"abcd"
    assert pcm.rate == 48000
    assert pcm.channels == 1
    assert buf.drain() is None  # izpraznjen


def test_byte_buffer_empty_drain_is_none():
    assert _ByteBuffer(rate=48000, channels=1).drain() is None


# ---------- MacCapture ----------

def test_start_without_helper_raises_helpful_error(tmp_path):
    capture = MacCapture(helper_path=tmp_path / "granova-system-audio")
    with pytest.raises(RuntimeError, match="setup.command"):
        capture.start()


def test_read_system_fills_buffer_until_eof():
    capture = MacCapture(helper_path=Path("neobstaja"))
    capture._proc = SimpleNamespace(stdout=io.BytesIO(b"x" * 10000))
    capture._system = _ByteBuffer(rate=48000, channels=1)
    capture._read_system()  # sinhrono: BytesIO ob koncu vrne b"" in zanka se ustavi
    system, mic = capture.drain()
    assert system.data == b"x" * 10000
    assert system.rate == 48000
    assert mic is None


def test_drain_before_start_returns_nothing():
    assert MacCapture(helper_path=Path("neobstaja")).drain() == (None, None)


# ---------- izbira platforme ----------

def test_get_capture_darwin_returns_mac_capture(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert isinstance(get_capture(), MacCapture)


def test_get_capture_unsupported_platform(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(NotImplementedError):
        get_capture()


def test_default_titles_fn_darwin_uses_quartz_reader(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert default_titles_fn() is _mac_window_titles


def test_default_titles_fn_unsupported_platform(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(NotImplementedError):
        default_titles_fn()
