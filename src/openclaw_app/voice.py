from __future__ import annotations

import importlib
import threading
from typing import Callable


class VoiceService:
    def __init__(self) -> None:
        pyttsx3_spec = importlib.util.find_spec("pyttsx3")
        sr_spec = importlib.util.find_spec("speech_recognition")

        self._pyttsx3 = importlib.import_module("pyttsx3") if pyttsx3_spec else None
        self._sr = importlib.import_module("speech_recognition") if sr_spec else None

        self._tts = self._pyttsx3.init() if self._pyttsx3 else None

    @property
    def tts_enabled(self) -> bool:
        return self._tts is not None

    @property
    def stt_enabled(self) -> bool:
        return self._sr is not None

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

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 12) -> str:
        if self._sr is None:
            raise RuntimeError("speech_recognition 未安装，无法使用麦克风识别")

        recognizer = self._sr.Recognizer()
        with self._sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        errors: list[str] = []
        try:
            return recognizer.recognize_google(audio, language="zh-CN")
        except Exception as exc:
            errors.append(f"Google识别失败: {exc}")

        try:
            return recognizer.recognize_sphinx(audio, language="zh-CN")
        except Exception as exc:
            errors.append(f"Sphinx识别失败: {exc}")

        raise RuntimeError("；".join(errors))
