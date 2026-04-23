from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass
class OpenClawEndpoint:
    base_url: str


class OpenClawClient:
    """Tiny HTTP client for talking to a local/remote OpenClaw service."""

    def __init__(self, endpoint: OpenClawEndpoint):
        self.endpoint = endpoint

    def health(self, timeout: float = 1.2) -> bool:
        for path in ("/health", "/api/health", "/v1/health", "/"):
            try:
                req = Request(self.endpoint.base_url + path, method="GET")
                with urlopen(req, timeout=timeout) as resp:
                    if 200 <= resp.status < 300:
                        return True
            except Exception:
                continue
        return False

    def chat(self, text: str, timeout: float = 20.0) -> str:
        for path in ("/api/chat", "/v1/chat", "/chat"):
            body = json.dumps({"message": text}).encode("utf-8")
            result = self._post_json(path, body, timeout)
            if isinstance(result, str):
                return result

        # OpenAI-compatible style endpoint fallback.
        body = json.dumps(
            {
                "model": "openclaw",
                "messages": [{"role": "user", "content": text}],
                "temperature": 0.7,
            }
        ).encode("utf-8")
        result = self._post_json("/v1/chat/completions", body, timeout)
        if isinstance(result, str):
            return result

        raise URLError("OpenClaw chat endpoint not found or request failed")

    def _post_json(self, path: str, body: bytes, timeout: float) -> str | None:
        try:
            req = Request(
                self.endpoint.base_url + path,
                data=body,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                if not raw.strip():
                    return None
                data = json.loads(raw)
                return self._extract_text(data)
        except Exception:
            return None

    @staticmethod
    def _extract_text(data: dict) -> str | None:
        for key in ("reply", "text", "message", "content", "response"):
            if key in data and isinstance(data[key], str):
                return data[key]

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                msg = first.get("message")
                if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                    return msg["content"]
                if isinstance(first.get("text"), str):
                    return first["text"]
        return None


def discover_openclaw(
    hosts: Iterable[str] = ("http://127.0.0.1", "http://localhost"),
    ports: Iterable[int] = (3000, 5173, 8000, 8080, 11434),
) -> OpenClawClient | None:
    for host in hosts:
        for port in ports:
            endpoint = OpenClawEndpoint(base_url=f"{host}:{port}")
            client = OpenClawClient(endpoint)
            if client.health():
                return client
    return None
