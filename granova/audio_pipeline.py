"""Mešanje surovih PCM virov v mono 16 kHz WAV za transkripcijo.

Namesto ffmpeg-a (ki na tem računalniku ni na voljo) mešamo v čistem Pythonu z
numpy — koščki so kratki (~15 s), zato je to poceni in odpravi sistemsko
odvisnost, kar poenostavi tudi kasnejše pakiranje.
"""
from __future__ import annotations

import io
import wave

import numpy as np

from granova.audio_capture import Pcm

TARGET_RATE = 16_000
SILENCE_RMS_THRESHOLD = 60.0  # int16 RMS, pod tem štejemo košček za tišino


def _to_mono_float(pcm: Pcm) -> np.ndarray:
    """int16 prepleteni vzorci -> mono float32 [-1, 1]."""
    samples = np.frombuffer(pcm.data, dtype=np.int16).astype(np.float32) / 32768.0
    if pcm.channels > 1:
        usable = len(samples) - (len(samples) % pcm.channels)
        samples = samples[:usable].reshape(-1, pcm.channels).mean(axis=1)
    return samples


def _resample(samples: np.ndarray, rate: int, target: int = TARGET_RATE) -> np.ndarray:
    if rate == target or len(samples) == 0:
        return samples
    n_out = int(round(len(samples) * target / rate))
    x_out = np.linspace(0, len(samples) - 1, n_out)
    return np.interp(x_out, np.arange(len(samples)), samples).astype(np.float32)


def mix_to_wav(system: Pcm | None, mic: Pcm | None) -> bytes:
    """Zmeša sistemski zvok in mikrofon v en mono 16 kHz WAV (bajti).

    Če je na voljo le en vir, vrne tega. Če ni nobenega, vrne prazen WAV.
    """
    tracks = [
        _resample(_to_mono_float(pcm), pcm.rate)
        for pcm in (system, mic)
        if pcm is not None and pcm.data
    ]
    if not tracks:
        mixed = np.zeros(0, dtype=np.float32)
    elif len(tracks) == 1:
        mixed = tracks[0]
    else:
        length = max(len(t) for t in tracks)
        mixed = np.zeros(length, dtype=np.float32)
        for t in tracks:
            mixed[: len(t)] += t
        mixed = np.clip(mixed, -1.0, 1.0)

    int16 = (mixed * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(TARGET_RATE)
        wf.writeframes(int16.tobytes())
    return buf.getvalue()


def is_silent(wav_bytes: bytes, threshold: float = SILENCE_RMS_THRESHOLD) -> bool:
    """True, če WAV vsebuje samo tišino (RMS pod pragom) — takih koščkov ne transkribiramo."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        raw = wf.readframes(wf.getnframes())
    if not raw:
        return True
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    rms = float(np.sqrt(np.mean(samples**2)))
    return rms < threshold
