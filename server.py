import asyncio
import json
import logging
import os
import signal
import threading

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import audio
import transcriber
from config import get_config, update_config
from main import main_loop
from state import AppState

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

file_handler = logging.FileHandler("mic-answer.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)

app = FastAPI()
state = AppState()


@app.get("/")
async def index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    queue = state.subscribe()
    try:
        # Send initial snapshot
        snapshot = state.get_snapshot()
        await ws.send_json({"type": "state", "status": snapshot["status"],
                            "rms": snapshot["rms"], "noise_floor": snapshot["noise_floor"]})
        await ws.send_json({"type": "config", **get_config()})
        for conv in snapshot["conversations"]:
            await ws.send_json({"type": "conversation", **conv})

        while True:
            msg = await queue.get()
            await ws.send_text(msg)
    except WebSocketDisconnect:
        pass
    finally:
        state.unsubscribe(queue)


@app.get("/api/config")
async def get_config_endpoint():
    return JSONResponse(get_config())


class ConfigUpdate(BaseModel):
    key: str
    value: str | float


@app.put("/api/config")
async def update_config_endpoint(body: ConfigUpdate):
    try:
        update_config(body.key, body.value)
    except KeyError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    # Broadcast updated config to all subscribers
    msg = json.dumps({"type": "config", **get_config()})
    state._notify(msg)
    return JSONResponse(get_config())


def _run_main_loop():
    logger.info("Starting main loop thread")
    main_loop(state=state)


def main():
    logger.info("Starting mic-answer with Web UI")

    transcriber.load_model()
    noise_floor = audio.calibrate_noise()
    state.update(noise_floor=noise_floor)

    loop = asyncio.new_event_loop()
    state.set_event_loop(loop)

    thread = threading.Thread(target=_run_main_loop, daemon=True)
    thread.start()

    config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)

    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(server.serve())
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down")
        os._exit(0)


if __name__ == "__main__":
    main()
