from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .core import ConversationEngine
from .voice import VoiceService


class OpenClawApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("OpenClaw Voice Avatar Demo")
        self.geometry("980x660")

        self.engine = ConversationEngine()
        self.voice = VoiceService()
        self.avatar_photo: tk.PhotoImage | None = None

        self._build_ui()
        self._update_status("idle")

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="角色风格").pack(side="left")
        self.style_var = tk.StringVar(value="商务")
        style_box = ttk.Combobox(
            top,
            textvariable=self.style_var,
            state="readonly",
            values=["商务", "动漫", "科幻", "写实", "可爱"],
            width=10,
        )
        style_box.pack(side="left", padx=(8, 16))
        style_box.bind("<<ComboboxSelected>>", self._on_style_change)

        ttk.Button(top, text="上传头像图片", command=self._upload_image).pack(side="left")
        ttk.Button(top, text="图片生成人物", command=self._generate_avatar).pack(side="left", padx=8)
        ttk.Button(top, text="开始通话", command=self._start_call).pack(side="left", padx=8)
        ttk.Button(top, text="结束通话", command=self._end_call).pack(side="left")
        ttk.Button(top, text="打断", command=self._interrupt).pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="状态: idle")
        ttk.Label(top, textvariable=self.status_var, foreground="#0055AA").pack(side="right")

        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        left = ttk.LabelFrame(main, text="人物预览", padding=8)
        left.pack(side="left", fill="y")

        self.avatar_label = ttk.Label(left, text="未上传图片\n(可使用默认形象)", width=28)
        self.avatar_label.pack()

        self.avatar_meta_var = tk.StringVar(value="类型: preset\n模型ID: -")
        ttk.Label(left, textvariable=self.avatar_meta_var).pack(pady=(10, 0))

        right = ttk.LabelFrame(main, text="通话记录", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.chat = tk.Text(right, height=26, wrap="word")
        self.chat.pack(fill="both", expand=True)
        self.chat.insert("end", "[系统] 已就绪。请先开始通话。\n")
        self.chat.configure(state="disabled")

        bottom = ttk.Frame(self, padding=12)
        bottom.pack(fill="x")

        self.input_var = tk.StringVar()
        entry = ttk.Entry(bottom, textvariable=self.input_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _e: self._send_text())

        ttk.Button(bottom, text="发送", command=self._send_text).pack(side="left", padx=8)
        ttk.Button(bottom, text="🎤 语音输入", command=self._voice_input).pack(side="left")

        stt = "可用" if self.voice.stt_enabled else "不可用(缺少 speech_recognition/pyaudio)"
        tts = "可用" if self.voice.tts_enabled else "不可用(缺少 pyttsx3)"
        ttk.Label(bottom, text=f"STT: {stt} | TTS: {tts}").pack(side="left", padx=12)

    def _append_chat(self, line: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", line + "\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _update_status(self, state: str) -> None:
        self.status_var.set(f"状态: {state}")

    def _refresh_avatar_meta(self) -> None:
        avatar = self.engine.avatar
        self.avatar_meta_var.set(f"类型: {avatar.avatar_type}\n模型ID: {avatar.model_id or '-'}")

    def _on_style_change(self, _event=None) -> None:
        style = self.style_var.get()
        self.engine.set_avatar_style(style)
        self._append_chat(f"[系统] 已切换风格: {style}")

    def _upload_image(self) -> None:
        path = filedialog.askopenfilename(
            title="选择头像图片",
            filetypes=[("Image", "*.png *.gif *.ppm *.pgm *.jpg *.jpeg"), ("All", "*.*")],
        )
        if not path:
            return

        try:
            self.engine.set_avatar_image(path)
            ext = Path(path).suffix.lower()
            if ext == ".png":
                self.avatar_photo = tk.PhotoImage(file=path)
                self.avatar_label.configure(image=self.avatar_photo, text="")
            else:
                self.avatar_label.configure(text=f"已上传: {Path(path).name}\n(非PNG仅显示文件名)")
            self._append_chat(f"[系统] 头像已更新: {Path(path).name}")
            self._refresh_avatar_meta()
        except Exception as exc:
            messagebox.showerror("上传失败", str(exc))

    def _generate_avatar(self) -> None:
        path = self.engine.avatar.image_path
        if not path:
            messagebox.showwarning("提示", "请先上传一张头像图片")
            return

        avatar = self.engine.generate_avatar_from_image(path)
        self.style_var.set(avatar.style)
        self._append_chat(f"[系统] 已根据图片生成人物: {avatar.name} ({avatar.model_id})")
        self._refresh_avatar_meta()

    def _start_call(self) -> None:
        self.engine.start_call()
        self._update_status(self.engine.state)
        self._append_chat("[系统] 通话已连接，开始说话吧。")

    def _end_call(self) -> None:
        self.engine.end_call()
        self._update_status(self.engine.state)
        self._append_chat("[系统] 通话已结束。")

    def _interrupt(self) -> None:
        self.engine.interrupt()
        self.voice.stop_speaking()
        self._update_status(self.engine.state)
        self._append_chat("[系统] 已打断当前播报，重新进入监听。")

    def _voice_input(self) -> None:
        if self.engine.state == "idle":
            messagebox.showwarning("提示", "请先点击“开始通话”。")
            return
        if not self.voice.stt_enabled:
            messagebox.showwarning("提示", "当前环境未安装语音识别依赖，请先安装 requirements 中的可选语音包")
            return

        self._append_chat("[系统] 正在监听麦克风，请说话...")
        self._update_status("listening")
        self.after(20, self._capture_and_send_voice)

    def _capture_and_send_voice(self) -> None:
        try:
            text = self.voice.listen_once()
            self.input_var.set(text)
            self._append_chat(f"[语音识别] {text}")
            self._send_text()
        except Exception as exc:
            self._append_chat(f"[系统] 语音识别失败: {exc}")

    def _send_text(self) -> None:
        if self.engine.state == "idle":
            messagebox.showwarning("提示", "请先点击“开始通话”。")
            return

        text = self.input_var.get().strip()
        if not text:
            return

        self.input_var.set("")
        self._append_chat(f"你: {text}")

        try:
            reply = self.engine.handle_user_text(text)
            self._update_status(self.engine.state)
            self._append_chat(f"OpenClaw: {reply}")
        except Exception as exc:
            messagebox.showerror("处理失败", str(exc))
            return

        self.voice.speak_async(reply, on_done=self._on_tts_done)

    def _on_tts_done(self) -> None:
        self.engine.after_reply()
        self.after(0, lambda: self._update_status(self.engine.state))


def run() -> None:
    app = OpenClawApp()
    app.mainloop()
