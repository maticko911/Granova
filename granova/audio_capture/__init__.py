"""Skupni vmesnik za zajem zvoka.

Vsaka platforma (Windows WASAPI, macOS ScreenCaptureKit) implementira
razred z metodami:

    start()            — začne zajem sistemskega zvoka in mikrofona v ozadju
    drain() -> (Pcm | None, Pcm | None)
                       — vrne surove PCM podatke (sistem, mikrofon), nabrane od
                         zadnjega klica, in izprazni medpomnilnik
    stop()             — ustavi zajem in sprosti naprave
"""
from dataclasses import dataclass


@dataclass
class Pcm:
    """Surovi int16 PCM posnetek enega vira."""

    data: bytes  # prepleteni int16 vzorci
    rate: int  # vzorčna frekvenca (Hz)
    channels: int  # število kanalov


def get_capture():
    """Vrne implementacijo zajema za trenutno platformo."""
    import sys

    if sys.platform == "win32":
        from granova.audio_capture.windows_wasapi import WasapiCapture

        return WasapiCapture()
    if sys.platform == "darwin":
        from granova.audio_capture.mac_capture import MacCapture

        return MacCapture()
    raise NotImplementedError(f"Zajem zvoka za {sys.platform} še ni podprt")
