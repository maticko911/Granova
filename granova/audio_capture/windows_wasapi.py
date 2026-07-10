"""Windows WASAPI zajem: sistemski zvok (loopback) + mikrofon.

Dva vira se zajemata neprekinjeno v ozadju (vsak v svoji niti); `drain()` vrne
vse, kar se je nabralo od zadnjega klica. Snemanje se s tem nikoli ne prekinja,
tudi medtem ko se prejšnji košček transkribira.
"""
from __future__ import annotations

import threading

from granova.audio_capture import Pcm

FRAMES_PER_BUFFER = 1024


class _StreamReader:
    """Bere en PyAudio tok v medpomnilnik, dokler ni ustavljen."""

    def __init__(self, pa, device: dict):
        import pyaudiowpatch as pyaudio

        self.rate = int(device["defaultSampleRate"])
        self.channels = max(1, int(device["maxInputChannels"]))
        self._stream = pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=device["index"],
            frames_per_buffer=FRAMES_PER_BUFFER,
        )
        self._frames: list[bytes] = []
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while self._running:
            try:
                chunk = self._stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
            except OSError:
                break
            with self._lock:
                self._frames.append(chunk)

    def drain(self) -> Pcm | None:
        with self._lock:
            frames, self._frames = self._frames, []
        if not frames:
            return None
        return Pcm(data=b"".join(frames), rate=self.rate, channels=self.channels)

    def stop(self) -> None:
        self._running = False
        self._thread.join(timeout=2)
        try:
            self._stream.stop_stream()
            self._stream.close()
        except OSError:
            pass


def _find_loopback(pa) -> dict:
    """Najde loopback različico privzetega izhoda (zvočniki/slušalke)."""
    import pyaudiowpatch as pyaudio

    wasapi = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
    speakers = pa.get_device_info_by_index(wasapi["defaultOutputDevice"])
    if speakers.get("isLoopbackDevice"):
        return speakers
    for lb in pa.get_loopback_device_info_generator():
        if speakers["name"] in lb["name"]:
            return lb
    raise RuntimeError("WASAPI loopback naprava ni najdena")


class WasapiCapture:
    """Zajem obeh virov na Windows prek pyaudiowpatch."""

    def __init__(self) -> None:
        self._pa = None
        self._system: _StreamReader | None = None
        self._mic: _StreamReader | None = None

    def start(self) -> None:
        import pyaudiowpatch as pyaudio

        self._pa = pyaudio.PyAudio()
        self._system = _StreamReader(self._pa, _find_loopback(self._pa))
        try:
            mic_info = self._pa.get_default_input_device_info()
            self._mic = _StreamReader(self._pa, mic_info)
        except OSError:
            self._mic = None  # brez mikrofona še vedno snemamo sistemski zvok

    def drain(self) -> tuple[Pcm | None, Pcm | None]:
        system = self._system.drain() if self._system else None
        mic = self._mic.drain() if self._mic else None
        return system, mic

    def stop(self) -> None:
        if self._system:
            self._system.stop()
        if self._mic:
            self._mic.stop()
        if self._pa:
            self._pa.terminate()
        self._system = self._mic = self._pa = None
