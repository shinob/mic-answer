import logging

import numpy as np
from faster_whisper import WhisperModel

from config import SAMPLE_RATE

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None


def _cuda_available() -> bool:
    """Check if CUDA is usable via ctranslate2."""
    try:
        import ctranslate2
        return "cuda" in ctranslate2.get_supported_compute_types("cuda")
    except Exception:
        return False


def load_model() -> None:
    """Load the faster-whisper model once at startup."""
    global _model
    device = "cuda" if _cuda_available() else "cpu"
    compute = "auto" if device == "cuda" else "int8"
    logger.info("Loading faster-whisper model (medium, %s)...", device)
    _model = WhisperModel("medium", device=device, compute_type=compute)
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
