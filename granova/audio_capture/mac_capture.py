"""macOS zajem: sistemski zvok (ScreenCaptureKit pomočnik) + mikrofon (sounddevice).

Pomočnik `granova-system-audio` (prevede ga setup.command) piše surovi mono
int16 @ 48 kHz PCM na stdout; tukaj ga podproces bere v niti v medpomnilnik.
Mikrofon zajema sounddevice (PortAudio). Kot na Windows: `drain()` vrne vse,
kar se je nabralo od zadnjega klica, snemanje pa se nikoli ne prekinja.
"""
from __future__ import annotations

import subprocess
import threading
from pathlib import Path

from granova.audio_capture import Pcm
from granova.config import APP_DIR

RATE = 48000
BLOCK_BYTES = 4096

HELPER_PATH = APP_DIR / "bin" / "granova-system-audio"


class _ByteBuffer:
    """Nitno varen medpomnilnik surovih PCM bajtov (testabilen brez naprav)."""

    def __init__(self, rate: int, channels: int) -> None:
        self.rate = rate
        self.channels = channels
        self._chunks: list[bytes] = []
        self._lock = threading.Lock()

    def append(self, chunk: bytes) -> None:
        with self._lock:
            self._chunks.append(chunk)

    def drain(self) -> Pcm | None:
        with self._lock:
            chunks, self._chunks = self._chunks, []
        if not chunks:
            return None
        return Pcm(data=b"".join(chunks), rate=self.rate, channels=self.channels)


class MacCapture:
    """Zajem obeh virov na macOS."""

    def __init__(self, helper_path: Path | None = None) -> None:
        self._helper_path = helper_path or HELPER_PATH
        self._proc: subprocess.Popen | None = None
        self._system: _ByteBuffer | None = None
        self._mic_buffer: _ByteBuffer | None = None
        self._mic_stream = None
        self._reader: threading.Thread | None = None

    def start(self) -> None:
        if not self._helper_path.exists():
            raise RuntimeError(
                "Pomočnik za sistemski zvok ni nameščen — zaženi setup.command "
                f"(pričakovan: {self._helper_path})"
            )
        self._proc = subprocess.Popen(
            [str(self._helper_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self._system = _ByteBuffer(rate=RATE, channels=1)
        self._reader = threading.Thread(target=self._read_system, daemon=True)
        self._reader.start()
        self._start_mic()

    def _read_system(self) -> None:
        proc, buf = self._proc, self._system
        while True:
            chunk = proc.stdout.read(BLOCK_BYTES)
            if not chunk:
                break
            buf.append(chunk)

    def _start_mic(self) -> None:
        try:
            import sounddevice

            self._mic_buffer = _ByteBuffer(rate=RATE, channels=1)

            def _callback(indata, frames, time_info, status) -> None:
                self._mic_buffer.append(bytes(indata))

            self._mic_stream = sounddevice.RawInputStream(
                samplerate=RATE,
                channels=1,
                dtype="int16",
                callback=_callback,
            )
            self._mic_stream.start()
        except Exception:  # brez mikrofona še vedno snemamo sistemski zvok
            self._mic_stream = None
            self._mic_buffer = None

    def drain(self) -> tuple[Pcm | None, Pcm | None]:
        system = self._system.drain() if self._system else None
        mic = self._mic_buffer.drain() if self._mic_buffer else None
        return system, mic

    def stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        if self._reader:
            self._reader.join(timeout=2)
        if self._mic_stream:
            try:
                self._mic_stream.stop()
                self._mic_stream.close()
            except Exception:
                pass
        self._proc = self._system = self._mic_buffer = None
        self._mic_stream = self._reader = None
