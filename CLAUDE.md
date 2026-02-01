# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daemon application (mic-answer) that continuously monitors microphone input, auto-detects speech via RMS levels, records and transcribes it, sends the text to an external API, and plays back a WAV audio response. Designed for reception/customer-service voice input scenarios.

See `projet.md` for the full specification (in Japanese).

## Core Loop

1. Monitor microphone (RMS-based speech detection)
2. Record audio (16kHz PCM, stop after 2s of silence)
3. Transcribe with speech recognition (Japanese)
4. POST JSON to external API, receive WAV response
5. Play response audio
6. Return to step 1

## Configuration

| Variable | Default | Description |
|---|---|---|
| SAMPLE_RATE | 16000 | Audio sample rate (Hz) |
| START_THRESHOLD | 0.02 | RMS level to start recording |
| SILENCE_THRESHOLD | 0.01 | RMS level considered silence |
| SILENCE_DURATION | 2.0 | Seconds of silence to stop recording |
| SEND_API_URL | http://localhost:8080/chat | External API endpoint |

## External API Contract

- **Request**: POST JSON `{"text":"...","speaker_id":0}` to the TTS endpoint
- **Response**: `200 OK` with `audio/wav` body (PCM 16bit), `X-Response-Text` header contains URL-encoded response text

## Key Constraints

- Speech recognition model must be loaded once at startup (not per-request)
- No concurrent recording/sending — strictly sequential cycles
- Must not crash on API communication failure (log error, return to listening)
- Must run in a Python virtual environment
- Intended to run as a systemd service with auto-restart
- Must work on CPU-only environments
