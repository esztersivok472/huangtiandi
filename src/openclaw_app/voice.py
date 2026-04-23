from __future__ import annotations

import threading
from typing import Callable

try:
    import pyttsx3  # type: ignore
except Exception:
    pyttsx3 = None

try:
    import speech_recognition as sr  # type: ignore
except Exception:
    sr = None


class VoiceService:
    def __init__(self) -> None:
        self._tts = pyttsx3.init() if pyttsx3 else None

    @property
    def tts_enabled(self) -> bool:
        return self._tts is not None

    @property
    def stt_enabled(self) -> bool:
        return sr is not None

    def speak_async(self, text: str, on_done: Callable[[], None]) -> None:
        def _worker() -> None:
            try:
                if self._tts:
                    self._tts.say(text)
                    self._tts.runAndWait()
            finally:
                on_done()

        threading.Thread(target=_worker, daemon=True).start()

    def stop_speaking(self) -> None:
        if self._tts:
            self._tts.stop()

    def listen_once(self, timeout: int = 4, phrase_time_limit: int = 12) -> str:
        if sr is None:
            raise RuntimeError("speech_recognition 未安装，无法使用麦克风识别")

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        # zh-CN 可以改成你需要的语言
        return recognizer.recognize_google(audio, language="zh-CN")
