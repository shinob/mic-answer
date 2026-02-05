import json
import logging
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

from config import SAMPLE_RATE

_DICTIONARY_PATH = Path(__file__).parent / "dictionary.json"

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None


def _cuda_available() -> bool:
    """Check if CUDA is usable via ctranslate2."""
    try:
        import ctranslate2
        supported = ctranslate2.get_supported_compute_types("cuda")
        logger.info("CUDA available: supported compute types=%s", supported)
        return len(supported) > 0
    except Exception:
        logger.warning("CUDA check failed", exc_info=True)
        return False


def load_model() -> None:
    """Load the faster-whisper model once at startup."""
    global _model
    device = "cuda" if _cuda_available() else "cpu"
    compute = "auto" if device == "cuda" else "int8"
    logger.info("Loading faster-whisper model (medium, %s)...", device)
    _model = WhisperModel("medium", device=device, compute_type=compute)
    logger.info("Model loaded")


def _load_dictionary() -> tuple[str | None, dict[str, str]]:
    """Load hotwords and replacements from dictionary.json.

    Returns (hotwords_str, replacements_dict).
    hotwords_str is a space-joined string of hotwords, or None if empty.
    On file-not-found or parse error, returns (None, {}) and logs a warning.
    """
    try:
        data = json.loads(_DICTIONARY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, {}
    except Exception:
        logger.warning("Failed to load %s", _DICTIONARY_PATH, exc_info=True)
        return None, {}

    hotwords_list = data.get("hotwords", [])
    hotwords_str = " ".join(hotwords_list) if hotwords_list else None
    replacements = data.get("replacements", {})
    return hotwords_str, replacements


def _apply_replacements(text: str, replacements: dict[str, str]) -> str:
    """Apply replacement dictionary to text, longest keys first."""
    for old, new in sorted(replacements.items(), key=lambda kv: len(kv[0]), reverse=True):
        text = text.replace(old, new)
    return text


def transcribe(audio: np.ndarray) -> str:
    """Transcribe audio numpy array (float32, mono) to text."""
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    # faster-whisper expects float32 mono 1-D array
    data = audio.flatten().astype(np.float32)

    hotwords, replacements = _load_dictionary()

    kwargs = dict(language="ja", beam_size=5, vad_filter=True)
    if hotwords:
        kwargs["hotwords"] = hotwords

    segments, info = _model.transcribe(data, **kwargs)
    text = "".join(seg.text for seg in segments).strip()
    logger.info("Transcription (raw): %s", text)

    if _is_hallucination(text):
        logger.warning("Filtered hallucination: %s", text)
        return ""

    if replacements:
        corrected = _apply_replacements(text, replacements)
        if corrected != text:
            logger.info("Transcription (corrected): %s", corrected)
            text = corrected

    return text


_HALLUCINATION_PHRASES = [
    "ご視聴ありがとうございました",
    "ご視聴ありがとうございます",
    "チャンネル登録お願いします",
    "チャンネル登録よろしくお願いします",
    "最後までご視聴ありがとうございました",
    "ありがとうございました",
]


def _is_hallucination(text: str) -> bool:
    """Check if the transcription is a known Whisper hallucination phrase."""
    return text in _HALLUCINATION_PHRASES
