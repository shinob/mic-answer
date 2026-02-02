import logging
import sys
import threading

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


_loop_lock = threading.Lock()


def main_loop(state=None) -> None:
    """Run the listen-record-transcribe-send-play loop.

    If state (AppState) is provided, status updates and conversation entries
    are pushed to it for the Web UI.
    """
    if not _loop_lock.acquire(blocking=False):
        logger.warning("main_loop already running, refusing to start a second instance")
        return

    try:
        _main_loop_inner(state)
    finally:
        _loop_lock.release()


def _main_loop_inner(state) -> None:
    def on_rms(level: float) -> None:
        if state is not None:
            state.update(rms=level)

    def on_output_rms(level: float) -> None:
        if state is not None:
            state.update(output_rms=level)

    while True:
        try:
            if state is not None:
                state.update(status="listening")

            initial_blocks = audio.wait_for_speech(on_rms=on_rms)

            if state is not None:
                state.update(status="recording")

            recorded = audio.record_until_silence(initial_blocks, on_rms=on_rms)

            if state is not None:
                state.update(status="transcribing")

            text = transcriber.transcribe(recorded)

            if not text:
                logger.info("Empty transcription, returning to listening")
                continue

            conversation_logger.info("Q: %s", text)

            if state is not None:
                state.update(status="sending", last_transcription=text)

            result = api_client.send_text(text)
            if result is None:
                continue

            wav_bytes, response_text = result
            conversation_logger.info("A: %s", response_text)

            if state is not None:
                state.add_conversation(text, response_text)
                state.update(status="playing")

            audio.play_wav(wav_bytes, on_rms=on_output_rms)
            audio.flush_mic()

        except KeyboardInterrupt:
            raise
        except Exception:
            logger.exception("Error in main loop")
        finally:
            if state is not None:
                state.update(status="idle", rms=0.0)


def main() -> None:
    logger.info("Starting mic-answer")
    transcriber.load_model()
    audio.calibrate_noise()
    logger.info("Entering main loop")
    main_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")
        sys.exit(0)
