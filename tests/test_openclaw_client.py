import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.openclaw_app.openclaw_client import OpenClawClient, OpenClawEndpoint


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(content_length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": "server_reply"}).encode("utf-8"))
            return

        if self.path == "/v1/chat/completions":
            content_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(content_length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"choices": [{"message": {"content": "openai_style_reply"}}]}).encode("utf-8")
            )
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


class _OpenAIOnlyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"choices": [{"message": {"content": "openai_only"}}]}).encode("utf-8")
            )
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


class OpenClawClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

        cls.server2 = HTTPServer(("127.0.0.1", 0), _OpenAIOnlyHandler)
        cls.port2 = cls.server2.server_port
        cls.thread2 = threading.Thread(target=cls.server2.serve_forever, daemon=True)
        cls.thread2.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server2.shutdown()
        cls.server2.server_close()

    def test_health_and_chat(self):
        client = OpenClawClient(OpenClawEndpoint(f"http://127.0.0.1:{self.port}"))
        self.assertTrue(client.health())
        self.assertEqual(client.chat("hello"), "server_reply")

    def test_openai_compatible_fallback(self):
        client = OpenClawClient(OpenClawEndpoint(f"http://127.0.0.1:{self.port2}"))
        self.assertTrue(client.health())
        self.assertEqual(client.chat("hello"), "openai_only")


if __name__ == "__main__":
    unittest.main()
