import logging
import io
import time
import wave

import numpy as np
import sounddevice as sd

from config import SAMPLE_RATE, START_THRESHOLD, SILENCE_THRESHOLD, SILENCE_DURATION

logger = logging.getLogger(__name__)

BLOCK_DURATION = 0.1  # 100ms per block
BLOCK_SIZE = int(SAMPLE_RATE * BLOCK_DURATION)


def _rms(data: np.ndarray) -> float:
    return float(np.sqrt(np.mean(data ** 2)))


def wait_for_speech() -> np.ndarray:
    """Block until speech is detected. Returns the first audio block that exceeded the threshold."""
    logger.info("Waiting for speech...")
    while True:
        block = sd.rec(BLOCK_SIZE, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        level = _rms(block)
        if level >= START_THRESHOLD:
            logger.info("Speech detected (RMS=%.4f)", level)
            return block


def record_until_silence(initial_block: np.ndarray) -> np.ndarray:
    """Record audio starting from initial_block until silence persists for SILENCE_DURATION seconds."""
    logger.info("Recording...")
    frames = [initial_block]
    silence_start: float | None = None

    while True:
        block = sd.rec(BLOCK_SIZE, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        frames.append(block)
        level = _rms(block)

        if level < SILENCE_THRESHOLD:
            if silence_start is None:
                silence_start = time.monotonic()
            elif time.monotonic() - silence_start >= SILENCE_DURATION:
                logger.info("Silence detected, stopping recording")
                break
        else:
            silence_start = None

    audio = np.concatenate(frames, axis=0)
    logger.info("Recorded %.2f seconds of audio", len(audio) / SAMPLE_RATE)
    return audio


def play_wav(wav_bytes: bytes) -> None:
    """Play WAV audio from bytes."""
    logger.info("Playing response audio...")
    with io.BytesIO(wav_bytes) as buf:
        with wave.open(buf, "rb") as wf:
            sr = wf.getframerate()
            channels = wf.getnchannels()
            raw = wf.readframes(wf.getnframes())
            dtype = {1: "int8", 2: "int16", 4: "int32"}[wf.getsampwidth()]
            data = np.frombuffer(raw, dtype=dtype).reshape(-1, channels)
    sd.play(data, samplerate=sr)
    sd.wait()
    logger.info("Playback finished")
