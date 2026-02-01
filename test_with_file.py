"""Test the pipeline with a WAV file instead of microphone input."""
import logging
import sys
import wave

import numpy as np

import audio
import transcriber
import api_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_wav(path: str) -> np.ndarray:
    with wave.open(path, "rb") as wf:
        raw = wf.readframes(wf.getnframes())
        sr = wf.getframerate()
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    logger.info("Loaded %s (%.2f sec, %d Hz)", path, len(data) / sr, sr)
    return data


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input.wav>")
        sys.exit(1)

    wav_path = sys.argv[1]

    transcriber.load_model()

    audio_data = load_wav(wav_path)
    text = transcriber.transcribe(audio_data)

    if not text:
        logger.info("Empty transcription")
        return

    result = api_client.send_text(text)
    if result is None:
        logger.info("API call failed (is the server running?)")
        return

    wav_bytes, response_text = result
    audio.play_wav(wav_bytes)


if __name__ == "__main__":
    main()
