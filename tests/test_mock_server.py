import json
from urllib.request import Request, urlopen
import unittest

from src.openclaw_app.mock_server import MockOpenClawServer


class MockServerTests(unittest.TestCase):
    def test_mock_server_health_and_chat(self):
        server = MockOpenClawServer()
        server.start()
        try:
            with urlopen(server.base_url + "/health", timeout=1.0) as resp:
                self.assertEqual(resp.status, 200)

            body = json.dumps({"message": "你好"}).encode("utf-8")
            req = Request(server.base_url + "/api/chat", data=body, method="POST", headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=1.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("Mock OpenClaw", data["reply"])
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
