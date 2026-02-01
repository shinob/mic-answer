import os

SAMPLE_RATE = int(os.environ.get("SAMPLE_RATE", 16000))
START_THRESHOLD = float(os.environ.get("START_THRESHOLD", 0.02))
SILENCE_THRESHOLD = float(os.environ.get("SILENCE_THRESHOLD", 0.01))
SILENCE_DURATION = float(os.environ.get("SILENCE_DURATION", 2.0))
SEND_API_URL = os.environ.get("SEND_API_URL", "http://localhost:8080/chat")
