# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daemon application (mic-answer) that continuously monitors microphone input, auto-detects speech via RMS levels, records and transcribes it, sends the text to an external API, and plays back a WAV audio response. Designed for reception/customer-service voice input scenarios.

See `projet.md` for the full specification (in Japanese).

## Commands

```bash
# Initial setup (installs libportaudio2, creates .venv, installs deps)
./setup.sh

# Run the daemon
./run.sh
# Or manually:
source .venv/bin/activate && python main.py

# Test pipeline with a WAV file (skips live mic input)
./test.sh
# Or manually:
source .venv/bin/activate && python test_with_file.py test.wav

# Deploy as systemd service (expects app at /opt/mic-answer)
sudo cp mic-answer.service /etc/systemd/system/
sudo systemctl enable --now mic-answer
```

There is no linter, formatter, or test suite configured. No pyproject.toml or setup.py — dependencies are managed via `requirements.txt`.

## Architecture

```
main.py          → Entry point; runs the infinite listen→record→transcribe→send→play loop
├── audio.py     → Microphone monitoring (RMS-based speech detection), recording, WAV playback (sounddevice/numpy)
├── transcriber.py → faster-whisper model loading (once) and Japanese transcription
├── api_client.py  → HTTP POST of transcribed text, receives WAV response
└── config.py      → Environment variable loading with defaults
```

**Execution is strictly sequential and single-threaded.** The main loop blocks on `wait_for_speech()`, then records, transcribes, sends, plays, and loops. All exceptions in the loop are caught so the daemon never crashes.

**Model lifecycle:** `transcriber.load_model()` is called once at startup. It auto-detects CUDA via ctranslate2 and falls back to CPU with int8 compute. Uses the "medium" whisper model with `beam_size=5`.

**Audio processing:** 100ms blocks (BLOCK_SIZE = 1600 samples at 16kHz). Speech starts when RMS exceeds `START_THRESHOLD`, recording stops after `SILENCE_DURATION` seconds below `SILENCE_THRESHOLD`.

## Configuration

| Variable | Default | Description |
|---|---|---|
| SAMPLE_RATE | 16000 | Audio sample rate (Hz) |
| START_THRESHOLD | 0.02 | RMS level to start recording |
| SILENCE_THRESHOLD | 0.01 | RMS level considered silence |
| SILENCE_DURATION | 2.0 | Seconds of silence to stop recording |
| SEND_API_URL | http://localhost:8080/chat | External API endpoint |

## External API Contract

- **Request**: POST JSON `{"text":"...","speaker_id":0}` to the configured endpoint
- **Response**: `200 OK` with `audio/wav` body (PCM 16bit), `X-Response-Text` header contains URL-encoded response text

## Key Constraints

- Speech recognition model must be loaded once at startup (not per-request)
- No concurrent recording/sending — strictly sequential cycles
- Must not crash on API communication failure (log error, return to listening)
- Must run in a Python virtual environment
- Intended to run as a systemd service with auto-restart
- Must work on CPU-only environments
