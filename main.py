import logging
import sys
import time

import audio
import transcriber
import api_client

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

file_handler = logging.FileHandler("mic-answer.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)
conversation_logger = logging.getLogger("conversation")


def main() -> None:
    logger.info("Starting mic-answer")

    transcriber.load_model()
    audio.calibrate_noise()

    logger.info("Entering main loop")
    while True:
        try:
            initial_blocks = audio.wait_for_speech()
            recorded = audio.record_until_silence(initial_blocks)
            text = transcriber.transcribe(recorded)

            if not text:
                logger.info("Empty transcription, returning to listening")
                continue

            conversation_logger.info("Q: %s", text)

            result = api_client.send_text(text)
            if result is None:
                continue

            wav_bytes, response_text = result
            conversation_logger.info("A: %s", response_text)
            audio.play_wav(wav_bytes)
            time.sleep(2)

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
