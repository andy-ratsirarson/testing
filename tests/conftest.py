"""Test fixtures: local HTML test server."""

import threading
import time
from pathlib import Path

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Build the test app
test_app = FastAPI()

SAMPLE_HTML = (Path(__file__).parent / "sample.html").read_text()


@test_app.get("/", response_class=HTMLResponse)
def index():
    return SAMPLE_HTML


@test_app.post("/submit", response_class=HTMLResponse)
def submit():
    return "<html><body><h1>Submission successful</h1></body></html>"


@test_app.get("/next", response_class=HTMLResponse)
def next_page():
    return "<html><body><h1>Next Page</h1></body></html>"


class ServerThread(threading.Thread):
    def __init__(self, app, host: str, port: int):
        super().__init__(daemon=True)
        self.app = app
        self.host = host
        self.port = port
        self.server = None

    def run(self):
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


@pytest.fixture(scope="session")
def test_server():
    """Start a test HTML server on a local port, yield base URL, shut down after."""
    host = "127.0.0.1"
    port = 9876
    thread = ServerThread(test_app, host, port)
    thread.start()
    # Wait for server to be ready
    import requests
    for _ in range(50):
        try:
            requests.get(f"http://{host}:{port}/", timeout=0.5)
            break
        except Exception:
            time.sleep(0.1)
    yield f"http://{host}:{port}"
    thread.stop()
