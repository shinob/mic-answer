import logging
import sys

import audio
import transcriber
import api_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting mic-answer")

    transcriber.load_model()

    logger.info("Entering main loop")
    while True:
        try:
            initial_block = audio.wait_for_speech()
            recorded = audio.record_until_silence(initial_block)
            text = transcriber.transcribe(recorded)

            if not text:
                logger.info("Empty transcription, returning to listening")
                continue

            result = api_client.send_text(text)
            if result is None:
                continue

            wav_bytes, response_text = result
            audio.play_wav(wav_bytes)

        except KeyboardInterrupt:
            raise
        except Exception:
            logger.exception("Error in main loop")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")
        sys.exit(0)
