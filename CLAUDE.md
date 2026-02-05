# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daemon application (mic-answer) that continuously monitors microphone input, auto-detects speech via RMS levels, records and transcribes it, sends the text to an external API, and plays back a WAV audio response. Designed for reception/customer-service voice input scenarios. Includes an optional Web UI with real-time status monitoring and a 3D VRM character.

See `projet.md` for the full specification (in Japanese).

## Commands

```bash
# Initial setup (installs libportaudio2, creates .venv, installs deps)
./setup.sh

# Run the daemon (headless, no Web UI)
./run.sh
# Or manually:
source .venv/bin/activate && python main.py

# Run with Web UI (http://localhost:8000)
./web.sh
# Or manually:
source .venv/bin/activate && python server.py

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
main.py            → Entry point; runs the infinite listen→record→transcribe→send→play loop
├── audio.py       → Microphone monitoring (RMS-based speech detection), recording, WAV playback
├── transcriber.py → faster-whisper model loading (once) and Japanese transcription
│   └── dictionary.json → Hotwords and replacement dictionary for proper noun correction
├── api_client.py  → HTTP POST of transcribed text, receives WAV response
├── config.py      → Environment variable loading with thread-safe dynamic updates
└── state.py       → AppState class for Web UI state management and WebSocket broadcasting

server.py          → FastAPI + Uvicorn Web UI server; spawns main loop in a background thread
static/
├── index.html     → Web UI dashboard (status, RMS meters, config panel, conversation log)
└── vrm-character.js → Three.js VRM/GLB 3D character with lip-sync, blink, and breathing
```

### Two entry points

- **`main.py`** — Headless daemon mode. Runs the main loop directly.
- **`server.py`** — Web UI mode. Starts FastAPI on port 8000, runs the main loop in a background thread, and bridges state updates to the browser via WebSocket (`/ws`). Also exposes `GET/PUT /api/config` for runtime config changes.

### Main loop pipeline

Execution is strictly sequential and single-threaded: `wait_for_speech()` → `record_until_silence()` → `transcribe()` → `send_text()` → `play_wav()` → 2s sleep → repeat. A thread lock (`_loop_lock`) prevents concurrent instances. All exceptions are caught so the daemon never crashes.

### Audio processing

100ms blocks (1600 samples at 16kHz). `calibrate_noise()` runs at startup for 3 seconds and sets a noise floor (`mean + 3×std` of RMS readings). Speech detection requires 3 consecutive blocks (300ms) above threshold. After playback, `flush_mic()` discards 1 second of input to avoid echo feedback.

### Model lifecycle

`transcriber.load_model()` is called once at startup. Auto-detects CUDA via ctranslate2, falls back to CPU with int8 compute. Uses the "medium" whisper model with `beam_size=5` and `vad_filter=True`. Known hallucination phrases (YouTube/thank-you patterns) are filtered and return empty string.

### Threading model

The main loop is single-threaded and sequential. Thread safety is needed in three places:
- `config.py` — `_lock` guards `get_config()`/`update_config()` for runtime changes from Web UI
- `state.py` — `_lock` guards state mutations; uses `loop.call_soon_threadsafe()` for async queue operations
- `main.py` — `_loop_lock` prevents concurrent main loop instances

### Logging

Two loggers — `__main__` for debug/info and `conversation` for Q&A pairs (prefixed `Q:` / `A:`). Both log to console and `/mic-answer.log`.

## Configuration

| Variable | Default | Description |
|---|---|---|
| SAMPLE_RATE | 16000 | Audio sample rate (Hz) |
| START_THRESHOLD | 0.1 | RMS level to trigger recording |
| SILENCE_THRESHOLD | 0.003 | RMS level (added to noise floor) to detect silence |
| SILENCE_DURATION | 2.0 | Seconds of silence to stop recording |
| SEND_API_URL | http://localhost:8080/chat | External API endpoint |

`START_THRESHOLD`, `SILENCE_THRESHOLD`, `SILENCE_DURATION`, and `SEND_API_URL` can be changed at runtime via the Web UI's `PUT /api/config` endpoint.

## External API Contract

- **Request**: POST JSON `{"text":"...","speaker_id":0}` to the configured endpoint (60s timeout)
- **Response**: `200 OK` with `audio/wav` body (PCM 16bit), `X-Response-Text` header contains URL-encoded response text

## Key Constraints

- Speech recognition model must be loaded once at startup (not per-request)
- No concurrent recording/sending — strictly sequential cycles
- Must not crash on API communication failure (log error, return to listening)
- Must run in a Python virtual environment
- Intended to run as a systemd service with auto-restart
- Must work on CPU-only environments
