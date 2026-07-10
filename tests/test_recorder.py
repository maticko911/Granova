import time

import numpy as np

from granova.audio_capture import Pcm
from granova.recorder import Recorder


def loud_pcm() -> Pcm:
    t = np.arange(16000) / 16000
    samples = (np.sin(2 * np.pi * 440 * t) * 0.3 * 32767).astype(np.int16)
    return Pcm(data=samples.tobytes(), rate=16000, channels=1)


class FakeCapture:
    """Vsak drain() vrne naslednji scenarij iz seznama (Pcm ali None)."""

    def __init__(self, script):
        self.script = list(script)
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def drain(self):
        pcm = self.script.pop(0) if self.script else None
        return pcm, None

    def stop(self):
        self.stopped = True


def wait_until(cond, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if cond():
            return True
        time.sleep(0.005)
    return False


def test_chunks_flow_to_callback_and_transcript():
    capture = FakeCapture([loud_pcm(), loud_pcm()])
    seen = []
    counter = iter(range(1, 100))
    rec = Recorder(
        capture=capture,
        transcribe_fn=lambda wav: f"košček {next(counter)}",
        on_chunk=seen.append,
        segment_seconds=0.02,
    )
    rec.start()
    assert wait_until(lambda: len(seen) >= 2)
    transcript = rec.stop()

    assert capture.started and capture.stopped
    assert seen[:2] == ["košček 1", "košček 2"]
    assert transcript.startswith("košček 1 košček 2")


def test_silent_chunks_are_not_transcribed():
    capture = FakeCapture([])  # drain vedno vrne (None, None) -> tišina
    calls = []
    rec = Recorder(
        capture=capture,
        transcribe_fn=lambda wav: calls.append(wav) or "x",
        segment_seconds=0.02,
    )
    rec.start()
    time.sleep(0.1)
    transcript = rec.stop()
    assert calls == []
    assert transcript == ""


def test_silence_timeout_fires():
    fired = []
    rec = Recorder(
        capture=FakeCapture([]),
        transcribe_fn=lambda wav: "",
        on_silence_timeout=lambda: fired.append(True),
        segment_seconds=0.02,
        silence_timeout_seconds=0.06,
    )
    rec.start()
    assert wait_until(lambda: fired)
    rec.stop()
    assert fired


def test_transcribe_error_does_not_kill_session():
    capture = FakeCapture([loud_pcm(), loud_pcm()])
    results = iter([RuntimeError("mreža"), "preživel"])

    def flaky(wav):
        r = next(results)
        if isinstance(r, Exception):
            raise r
        return r

    seen = []
    rec = Recorder(capture=capture, transcribe_fn=flaky, on_chunk=seen.append, segment_seconds=0.02)
    rec.start()
    assert wait_until(lambda: seen)
    rec.stop()
    assert seen == ["preživel"]
