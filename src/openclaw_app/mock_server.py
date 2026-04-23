from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health", "/api/health", "/v1/health"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path in ("/api/chat", "/chat", "/v1/chat", "/v1/chat/completions"):
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8", errors="ignore") if length else ""
            text = ""
            try:
                data = json.loads(raw) if raw else {}
                text = data.get("message") or ""
                if not text and isinstance(data.get("messages"), list) and data["messages"]:
                    text = data["messages"][-1].get("content", "")
            except Exception:
                text = ""

            reply = f"[Mock OpenClaw] 收到：{text or '（空）'}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


class MockOpenClawServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self.server = HTTPServer((host, port), _Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def start(self) -> None:
        if not self.thread.is_alive():
            self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
