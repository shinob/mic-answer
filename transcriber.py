import logging

import numpy as np
from faster_whisper import WhisperModel

from config import SAMPLE_RATE

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None


def load_model() -> None:
    """Load the faster-whisper model once at startup."""
    global _model
    logger.info("Loading faster-whisper model (medium, cuda)...")
    _model = WhisperModel("medium", device="cuda", compute_type="auto")
    logger.info("Model loaded")


def transcribe(audio: np.ndarray) -> str:
    """Transcribe audio numpy array (float32, mono) to text."""
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    # faster-whisper expects float32 mono 1-D array
    data = audio.flatten().astype(np.float32)

    segments, info = _model.transcribe(data, language="ja", beam_size=5)
    text = "".join(seg.text for seg in segments).strip()
    logger.info("Transcription: %s", text)
    return text
