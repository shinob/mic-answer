import asyncio
import json
import threading
import time
from datetime import datetime, timezone


class AppState:
    def __init__(self):
        self._lock = threading.Lock()
        self.status: str = "idle"
        self.rms: float = 0.0
        self.output_rms: float = 0.0
        self.noise_floor: float = 0.0
        self.conversations: list[dict] = []
        self.last_transcription: str = ""
        self._subscribers: list[asyncio.Queue] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def update(self, *, status: str | None = None, rms: float | None = None,
               output_rms: float | None = None,
               noise_floor: float | None = None, last_transcription: str | None = None) -> None:
        with self._lock:
            if status is not None:
                self.status = status
            if rms is not None:
                self.rms = rms
            if output_rms is not None:
                self.output_rms = output_rms
            if noise_floor is not None:
                self.noise_floor = noise_floor
            if last_transcription is not None:
                self.last_transcription = last_transcription
            msg = json.dumps({
                "type": "state",
                "status": self.status,
                "rms": self.rms,
                "output_rms": self.output_rms,
                "noise_floor": self.noise_floor,
            })
        self._notify(msg)

    def add_conversation(self, q: str, a: str) -> None:
        entry = {
            "q": q,
            "a": a,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self.conversations.append(entry)
        msg = json.dumps({"type": "conversation", **entry})
        self._notify(msg)

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        with self._lock:
            try:
                self._subscribers.remove(queue)
            except ValueError:
                pass

    def get_snapshot(self) -> dict:
        with self._lock:
            return {
                "status": self.status,
                "rms": self.rms,
                "output_rms": self.output_rms,
                "noise_floor": self.noise_floor,
                "conversations": list(self.conversations),
            }

    def _notify(self, msg: str) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for queue in subscribers:
            try:
                if self._loop is not None and self._loop.is_running():
                    self._loop.call_soon_threadsafe(queue.put_nowait, msg)
                else:
                    queue.put_nowait(msg)
            except asyncio.QueueFull:
                pass
