import logging
from urllib.parse import unquote

import requests

from config import SEND_API_URL

logger = logging.getLogger(__name__)


def send_text(text: str) -> tuple[bytes, str] | None:
    """Send transcribed text to the external API.

    Returns (wav_bytes, response_text) on success, or None on failure.
    """
    payload = {"text": text, "speaker_id": 0}
    logger.info("Sending to API: %s", text)

    try:
        resp = requests.post(SEND_API_URL, json=payload, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("API request failed: %s", e)
        return None

    response_text = unquote(resp.headers.get("X-Response-Text", ""))
    logger.info("API response text: %s", response_text)
    return resp.content, response_text
