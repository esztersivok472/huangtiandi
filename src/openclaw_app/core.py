from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import List, Literal

CallState = Literal["idle", "listening", "thinking", "replying"]
AvatarType = Literal["preset", "generated"]


@dataclass
class Message:
    role: Literal["user", "assistant"]
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AvatarProfile:
    name: str
    style: str
    avatar_type: AvatarType = "preset"
    image_path: str | None = None
    model_id: str | None = None
    model_path: str | None = None


class ConversationEngine:
    """Conversation core for a phone-like avatar assistant."""

    def __init__(self) -> None:
        self.state: CallState = "idle"
        self.history: List[Message] = []
        self.avatar = AvatarProfile(name="OpenClaw", style="商务")

    def set_avatar_style(self, style: str) -> None:
        if not style.strip():
            raise ValueError("style cannot be empty")
        self.avatar.style = style.strip()

    def set_avatar_image(self, image_path: str) -> None:
        path = Path(image_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")
        self.avatar.image_path = str(path)

    def generate_avatar_from_image(self, image_path: str) -> AvatarProfile:
        """Simulate image->avatar generation for MVP.

        The output keeps a stable model_id based on file content hash.
        """
        path = Path(image_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        data = path.read_bytes()
        digest = hashlib.sha1(data).hexdigest()[:12]
        self.avatar.avatar_type = "generated"
        self.avatar.image_path = str(path)
        self.avatar.model_id = f"mdl_{digest}"
        self.avatar.name = f"用户形象_{digest[:6]}"
        self.avatar.style = "上传生成"
        return self.avatar

    def start_call(self) -> None:
        self.state = "listening"

    def end_call(self) -> None:
        self.state = "idle"

    def interrupt(self) -> None:
        self.state = "listening"

    def handle_user_text(self, text: str) -> str:
        clean = text.strip()
        if not clean:
            raise ValueError("text cannot be empty")

        self.state = "thinking"
        self.history.append(Message(role="user", text=clean))

        reply = self._generate_reply(clean)
        self.history.append(Message(role="assistant", text=reply))
        self.state = "replying"
        return reply

    def after_reply(self) -> None:
        self.state = "listening"

    def _generate_reply(self, text: str) -> str:
        if "你好" in text or "hello" in text.lower():
            return (
                f"你好，我是{self.avatar.name}，当前风格是{self.avatar.style}。"
                "我可以继续和你电话式聊天。"
            )
        return f"我听到你说：{text}。如果你在说话时我正在播报，你可以点击“打断”。"
