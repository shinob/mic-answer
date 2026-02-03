import os
import threading

SAMPLE_RATE = int(os.environ.get("SAMPLE_RATE", 16000))
START_THRESHOLD = float(os.environ.get("START_THRESHOLD", 0.05))
SILENCE_THRESHOLD = float(os.environ.get("SILENCE_THRESHOLD", 0.003))
SILENCE_DURATION = float(os.environ.get("SILENCE_DURATION", 2.0))
SEND_API_URL = os.environ.get("SEND_API_URL", "http://localhost:8080/chat")

_lock = threading.Lock()

_CONFIGURABLE = {
    "START_THRESHOLD": float,
    "SILENCE_THRESHOLD": float,
    "SILENCE_DURATION": float,
    "SEND_API_URL": str,
}


def get_config() -> dict:
    with _lock:
        return {key: globals()[key] for key in _CONFIGURABLE}


def update_config(key: str, value) -> None:
    if key not in _CONFIGURABLE:
        raise KeyError(f"Unknown config key: {key}")
    cast = _CONFIGURABLE[key]
    with _lock:
        globals()[key] = cast(value)
