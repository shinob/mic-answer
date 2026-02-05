import logging
import io
import time
import wave
from collections.abc import Callable

import numpy as np
import sounddevice as sd

from config import SAMPLE_RATE

logger = logging.getLogger(__name__)

BLOCK_DURATION = 0.1  # 100ms per block
BLOCK_SIZE = int(SAMPLE_RATE * BLOCK_DURATION)

CALIBRATION_DURATION = 3.0  # seconds to measure ambient noise
CALIBRATION_BLOCKS = int(CALIBRATION_DURATION / BLOCK_DURATION)

SPEECH_CONFIRM_BLOCKS = 3  # consecutive blocks above threshold to confirm speech (300ms)

_noise_floor: float = 0.0


def _rms(data: np.ndarray) -> float:
    centered = data - np.mean(data)
    return float(np.sqrt(np.mean(centered ** 2)))


def calibrate_noise() -> float:
    """Measure ambient noise level and set the noise floor baseline. Returns the noise floor."""
    global _noise_floor
    from config import START_THRESHOLD
    logger.info("Calibrating ambient noise level (%.1fs)...", CALIBRATION_DURATION)
    levels = []
    for _ in range(CALIBRATION_BLOCKS):
        block = sd.rec(BLOCK_SIZE, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        levels.append(_rms(block))
    arr = np.array(levels)
    _noise_floor = float(np.mean(arr) + 3 * np.std(arr))
    logger.info("Noise floor calibrated: mean=%.6f std=%.6f floor=%.6f (effective start threshold=%.4f)",
                float(np.mean(arr)), float(np.std(arr)), _noise_floor, _noise_floor + START_THRESHOLD)
    return _noise_floor


def wait_for_speech(on_rms: Callable[[float], None] | None = None) -> list[np.ndarray]:
    """Block until speech is detected. Returns the audio blocks that confirmed speech."""
    from config import START_THRESHOLD
    #effective_threshold = _noise_floor + START_THRESHOLD
    effective_threshold = START_THRESHOLD
    logger.info("Waiting for speech (threshold=%.4f)...", effective_threshold)
    consecutive = 0
    pending_blocks: list[np.ndarray] = []
    while True:
        block = sd.rec(BLOCK_SIZE, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        level = _rms(block)
        if on_rms is not None:
            on_rms(level)
        if level >= effective_threshold:
            consecutive += 1
            pending_blocks.append(block)
            if consecutive >= SPEECH_CONFIRM_BLOCKS:
                logger.info("Speech detected (RMS=%.4f, %d consecutive blocks)",
                            level, consecutive)
                return pending_blocks
        else:
            consecutive = 0
            pending_blocks.clear()


def record_until_silence(initial_blocks: list[np.ndarray],
                         on_rms: Callable[[float], None] | None = None) -> np.ndarray:
    """Record audio starting from initial_blocks until silence persists for SILENCE_DURATION seconds."""
    from config import SILENCE_THRESHOLD, SILENCE_DURATION
    logger.info("Recording...")
    frames = list(initial_blocks)
    silence_start: float | None = None

    while True:
        block = sd.rec(BLOCK_SIZE, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        frames.append(block)
        level = _rms(block)
        if on_rms is not None:
            on_rms(level)

        if level < _noise_floor + SILENCE_THRESHOLD:
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


def play_wav(wav_bytes: bytes, on_rms: Callable[[float], None] | None = None) -> None:
    """Play WAV audio from bytes. If on_rms is provided, report output RMS per block."""
    logger.info("Playing response audio...")
    with io.BytesIO(wav_bytes) as buf:
        with wave.open(buf, "rb") as wf:
            sr = wf.getframerate()
            channels = wf.getnchannels()
            raw = wf.readframes(wf.getnframes())
            dtype_map = {1: "int8", 2: "int16", 4: "int32"}
            sample_width = wf.getsampwidth()
            dtype = dtype_map[sample_width]
            data = np.frombuffer(raw, dtype=dtype).reshape(-1, channels)

    if on_rms is None:
        sd.play(data, samplerate=sr)
        sd.wait()
    else:
        block_size = int(sr * BLOCK_DURATION)
        float_data = data.astype(np.float32) / (2 ** (sample_width * 8 - 1))
        with sd.OutputStream(samplerate=sr, channels=channels, dtype="float32") as stream:
            for offset in range(0, len(float_data), block_size):
                block = float_data[offset:offset + block_size]
                stream.write(block)
                on_rms(_rms(block))
        on_rms(0.0)
    logger.info("Playback finished")


def flush_mic(duration: float = 1.0) -> None:
    """Discard microphone input for the given duration to avoid echo feedback."""
    blocks = int(duration / BLOCK_DURATION)
    logger.info("Flushing mic input (%.1fs)...", duration)
    for _ in range(blocks):
        sd.rec(BLOCK_SIZE, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
