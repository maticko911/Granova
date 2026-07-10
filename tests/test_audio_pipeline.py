import io
import wave

import numpy as np

from granova import audio_pipeline
from granova.audio_capture import Pcm


def make_pcm(freq: float, seconds: float = 1.0, rate: int = 48000, channels: int = 2, amp: float = 0.3) -> Pcm:
    t = np.arange(int(rate * seconds)) / rate
    mono = (np.sin(2 * np.pi * freq * t) * amp * 32767).astype(np.int16)
    interleaved = np.repeat(mono, channels)
    return Pcm(data=interleaved.tobytes(), rate=rate, channels=channels)


def wav_info(wav_bytes: bytes):
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        return wf.getnchannels(), wf.getframerate(), wf.getnframes()


def test_mix_two_sources_to_mono_16k():
    system = make_pcm(440, rate=48000)
    mic = make_pcm(300, rate=44100)
    wav = audio_pipeline.mix_to_wav(system, mic)
    channels, rate, frames = wav_info(wav)
    assert channels == 1
    assert rate == 16000
    # dolžina ~1 s (vzame daljšo sled)
    assert abs(frames - 16000) < 100
    assert not audio_pipeline.is_silent(wav)


def test_mix_single_source():
    wav = audio_pipeline.mix_to_wav(make_pcm(440), None)
    channels, rate, _ = wav_info(wav)
    assert (channels, rate) == (1, 16000)
    assert not audio_pipeline.is_silent(wav)


def test_mix_no_sources_is_silent_empty_wav():
    wav = audio_pipeline.mix_to_wav(None, None)
    channels, rate, frames = wav_info(wav)
    assert (channels, rate, frames) == (1, 16000, 0)
    assert audio_pipeline.is_silent(wav)


def test_silence_detection():
    quiet = Pcm(data=np.zeros(48000, dtype=np.int16).tobytes(), rate=48000, channels=1)
    wav = audio_pipeline.mix_to_wav(quiet, None)
    assert audio_pipeline.is_silent(wav)
