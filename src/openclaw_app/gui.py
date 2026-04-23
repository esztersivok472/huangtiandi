from __future__ import annotations

import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import webbrowser

from .core import ConversationEngine
from .launcher import default_openclaw_workdir, find_openclaw_executable, start_openclaw
from .mock_server import MockOpenClawServer
from .openclaw_client import OpenClawClient, OpenClawEndpoint, discover_openclaw
from .voice import VoiceService


class OpenClawApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("OpenClaw Voice Avatar Demo")
        self.geometry("1100x760")

        self.engine = ConversationEngine()
        self.voice = VoiceService()
        self.openclaw_client: OpenClawClient | None = None
        self.openclaw_process = None
        self._avatar_enabled = False
        self.mock_server: MockOpenClawServer | None = None
        self._discovering = False

        self.avatar_photo: tk.PhotoImage | None = None
        self.continuous_mode = tk.BooleanVar(value=False)
        self._continuous_running = False

        self._build_ui()
        self._update_status("idle")
        self.after(150, self._auto_discover_openclaw)

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
        ttk.Button(top, text="上传3D模型", command=self._upload_3d_model).pack(side="left", padx=8)
        ttk.Button(top, text="打开3D预览", command=self._open_3d_preview).pack(side="left")
        ttk.Button(top, text="图片生成人物", command=self._generate_avatar).pack(side="left", padx=8)
        ttk.Button(top, text="开始通话", command=self._start_call).pack(side="left", padx=8)
        ttk.Button(top, text="结束通话", command=self._end_call).pack(side="left")
        ttk.Button(top, text="打断", command=self._interrupt).pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="状态: idle")
        ttk.Label(top, textvariable=self.status_var, foreground="#0055AA").pack(side="right")

        oc = ttk.Frame(self, padding=(12, 0, 12, 6))
        oc.pack(fill="x")
        ttk.Label(oc, text="OpenClaw程序路径:").pack(side="left")
        self.exec_var = tk.StringVar(value="")
        ttk.Entry(oc, textvariable=self.exec_var, width=44).pack(side="left", padx=(6, 4))
        ttk.Label(oc, text="工作目录:").pack(side="left", padx=(8, 2))
        self.workdir_var = tk.StringVar(value=str(default_openclaw_workdir()))
        ttk.Entry(oc, textvariable=self.workdir_var, width=28).pack(side="left", padx=(0, 4))
        ttk.Button(oc, text="自动查找", command=self._find_openclaw_exec).pack(side="left")
        ttk.Button(oc, text="启动OpenClaw", command=self._start_openclaw_exec).pack(side="left", padx=6)
        ttk.Button(oc, text="启动模拟OpenClaw", command=self._start_mock_openclaw).pack(side="left", padx=6)

        conn = ttk.Frame(self, padding=(12, 0, 12, 8))
        conn.pack(fill="x")

        ttk.Label(conn, text="OpenClaw地址:").pack(side="left")
        self.endpoint_var = tk.StringVar(value="自动检测中...")
        ttk.Entry(conn, textvariable=self.endpoint_var, width=44).pack(side="left", padx=(8, 6))
        ttk.Button(conn, text="自动检测", command=self._auto_discover_openclaw).pack(side="left")
        ttk.Button(conn, text="连接测试", command=self._manual_connect_openclaw).pack(side="left", padx=6)

        self.conn_var = tk.StringVar(value="OpenClaw: 未连接")
        ttk.Label(conn, textvariable=self.conn_var, foreground="#6B5A00").pack(side="left", padx=10)

        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        left = ttk.LabelFrame(main, text="人物预览", padding=8)
        left.pack(side="left", fill="y")

        self.avatar_canvas = tk.Canvas(left, width=220, height=220, bg="#f8f8f8", highlightthickness=0)
        self.avatar_canvas.pack()
        self._draw_default_avatar()

        self.avatar_meta_var = tk.StringVar(value="类型: preset\n模型ID: -\n3D模型: -")
        ttk.Label(left, textvariable=self.avatar_meta_var).pack(pady=(10, 0))

        right = ttk.LabelFrame(main, text="通话记录", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.chat = tk.Text(right, height=30, wrap="word")
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
        ttk.Button(bottom, text="🎤 语音输入", command=self._voice_input_once).pack(side="left")
        ttk.Checkbutton(bottom, text="连续语音", variable=self.continuous_mode).pack(side="left", padx=8)
        ttk.Button(bottom, text="开始连续听说", command=self._start_continuous_voice).pack(side="left")

        stt = "可用" if self.voice.stt_enabled else "不可用(缺少 speech_recognition/pyaudio)"
        tts = "可用" if self.voice.tts_enabled else "不可用(缺少 pyttsx3)"
        ttk.Label(bottom, text=f"STT: {stt} | TTS: {tts}").pack(side="left", padx=12)

    def _draw_default_avatar(self) -> None:
        c = self.avatar_canvas
        c.delete("all")
        c.create_oval(40, 30, 180, 170, fill="#FFD39B", outline="#C79A5B", width=2)
        c.create_oval(75, 80, 88, 93, fill="black")
        c.create_oval(132, 80, 145, 93, fill="black")
        c.create_arc(82, 100, 142, 132, start=200, extent=140, style="arc", width=3)
        c.create_text(110, 196, text="OpenClaw", fill="#1f4c8f", font=("Arial", 14, "bold"))

    def _append_chat(self, line: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", line + "\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _update_status(self, state: str) -> None:
        self.status_var.set(f"状态: {state}")

    def _refresh_avatar_meta(self) -> None:
        avatar = self.engine.avatar
        model_name = Path(avatar.model_path).name if avatar.model_path else "-"
        self.avatar_meta_var.set(f"类型: {avatar.avatar_type}\n模型ID: {avatar.model_id or '-'}\n3D模型: {model_name}")

    def _find_openclaw_exec(self) -> None:
        path = find_openclaw_executable()
        if path:
            self.exec_var.set(path)
            self._append_chat(f"[系统] 已找到 OpenClaw 程序: {path}")
        else:
            self._append_chat("[系统] 未找到 OpenClaw 程序，请手动安装或填写路径。")

    def _start_openclaw_exec(self) -> None:
        path = self.exec_var.get().strip()
        if not path:
            self._find_openclaw_exec()
            path = self.exec_var.get().strip()
        if not path:
            return

        try:
            self.openclaw_process = start_openclaw(path, workdir=self.workdir_var.get().strip() or None)
            self._append_chat("[系统] 已尝试启动 OpenClaw 程序，正在自动检测连接...")
            self.after(1200, self._auto_discover_openclaw)
        except Exception as exc:
            self._append_chat(f"[系统] 启动 OpenClaw 失败: {exc}")

    def _set_connected(self, client: OpenClawClient | None) -> None:
        self.openclaw_client = client
        if client:
            self.conn_var.set(f"OpenClaw: 已连接 ({client.endpoint.base_url})")
            self.endpoint_var.set(client.endpoint.base_url)
            self._activate_connected_features()
        else:
            self.conn_var.set("OpenClaw: 未连接（将使用本地离线回复）")
            self.endpoint_var.set("未发现服务")

    def _activate_connected_features(self) -> None:
        if self._avatar_enabled:
            return
        self._avatar_enabled = True
        self.continuous_mode.set(True)
        self._append_chat("[系统] 已连接 OpenClaw：已自动启用虚拟形象与连续语音模式。")

    def _auto_discover_openclaw(self) -> None:
        if self._discovering:
            return
        self._discovering = True
        self.endpoint_var.set("自动检测中...")

        def _job() -> None:
            client = discover_openclaw(ports=(3000, 5173, 8000, 8080, 11434, 5000, 7860))

            def _finish() -> None:
                self._discovering = False
                self._set_connected(client)
                if client:
                    self._append_chat(f"[系统] 自动连接到 OpenClaw: {client.endpoint.base_url}")
                else:
                    self._append_chat("[系统] 自动检测完成：未发现 OpenClaw 服务，可点击“启动模拟OpenClaw”先测试。")

            self.after(0, _finish)

        threading.Thread(target=_job, daemon=True).start()


    def _start_mock_openclaw(self) -> None:
        if self.mock_server is None:
            self.mock_server = MockOpenClawServer()
            self.mock_server.start()
        url = self.mock_server.base_url
        self.endpoint_var.set(url)
        self._append_chat(f"[系统] 模拟OpenClaw已启动: {url}")
        self._manual_connect_openclaw()

    def _manual_connect_openclaw(self) -> None:
        url = self.endpoint_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入 OpenClaw 地址，例如 http://127.0.0.1:3000")
            return
        client = OpenClawClient(OpenClawEndpoint(url))
        if client.health():
            self._set_connected(client)
            self._append_chat(f"[系统] OpenClaw 连接成功: {url}")
        else:
            self._set_connected(None)
            self._append_chat(f"[系统] OpenClaw 连接失败: {url}")

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
            self.avatar_canvas.delete("all")
            if ext == ".png":
                self.avatar_photo = tk.PhotoImage(file=path)
                self.avatar_canvas.create_image(110, 110, image=self.avatar_photo)
            else:
                self._draw_default_avatar()
                self.avatar_canvas.create_text(110, 18, text=f"已上传: {Path(path).name}", fill="#333")
            self._append_chat(f"[系统] 头像已更新: {Path(path).name}")
            self._refresh_avatar_meta()
        except Exception as exc:
            messagebox.showerror("上传失败", str(exc))

    def _upload_3d_model(self) -> None:
        path = filedialog.askopenfilename(
            title="选择3D模型",
            filetypes=[("3D Model", "*.glb *.gltf *.obj *.fbx"), ("All", "*.*")],
        )
        if not path:
            return
        self.engine.avatar.model_path = path
        self._append_chat(f"[系统] 3D模型已加载: {Path(path).name}")
        self._refresh_avatar_meta()

    def _open_3d_preview(self) -> None:
        model_path = self.engine.avatar.model_path
        if not model_path:
            messagebox.showwarning("提示", "请先上传3D模型（建议 .glb）")
            return

        path_uri = Path(model_path).resolve().as_uri()
        html = f"""
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <script type='module' src='https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js'></script>
  <style>body{{margin:0;background:#111}} model-viewer{{width:100vw;height:100vh;}}</style>
</head>
<body>
  <model-viewer src='{path_uri}' camera-controls auto-rotate shadow-intensity='1'></model-viewer>
</body>
</html>
"""
        tmp = Path(tempfile.gettempdir()) / "openclaw_3d_preview.html"
        tmp.write_text(html, encoding="utf-8")
        webbrowser.open(tmp.as_uri())
        self._append_chat("[系统] 已在浏览器打开3D预览（model-viewer）。")

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
        self._continuous_running = False
        self.engine.end_call()
        self._update_status(self.engine.state)
        self._append_chat("[系统] 通话已结束。")

    def _interrupt(self) -> None:
        self.engine.interrupt()
        self.voice.stop_speaking()
        self._update_status(self.engine.state)
        self._append_chat("[系统] 已打断当前播报，重新进入监听。")

    def _voice_input_once(self) -> None:
        if self.engine.state == "idle":
            messagebox.showwarning("提示", "请先点击“开始通话”。")
            return
        if not self.voice.stt_enabled:
            messagebox.showwarning("提示", "当前环境未安装语音识别依赖，请先安装 requirements 中的可选语音包")
            return

        self._append_chat("[系统] 正在监听麦克风，请说话（最多12秒）...")
        self._update_status("listening")

        def _job() -> None:
            try:
                text = self.voice.listen_once()
                self.after(0, lambda: self._on_voice_text(text))
            except Exception as exc:
                self.after(0, lambda: self._append_chat(f"[系统] 语音识别失败: {exc}"))

        threading.Thread(target=_job, daemon=True).start()

    def _start_continuous_voice(self) -> None:
        if self.engine.state == "idle":
            messagebox.showwarning("提示", "请先点击“开始通话”。")
            return
        if not self.continuous_mode.get():
            messagebox.showinfo("提示", "请先勾选“连续语音”")
            return
        if not self.voice.stt_enabled:
            messagebox.showwarning("提示", "当前环境未安装语音识别依赖")
            return
        if self._continuous_running:
            self._append_chat("[系统] 连续语音已在运行中。")
            return

        self._continuous_running = True
        self._append_chat("[系统] 连续语音已开启，结束通话将自动停止。")

        def _loop() -> None:
            while self._continuous_running and self.engine.state != "idle":
                try:
                    text = self.voice.listen_once(timeout=4, phrase_time_limit=10)
                    self.after(0, lambda t=text: self._on_voice_text(t))
                except Exception:
                    continue

        threading.Thread(target=_loop, daemon=True).start()

    def _on_voice_text(self, text: str) -> None:
        self.input_var.set(text)
        self._append_chat(f"[语音识别] {text}")
        self._send_text()

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
            if self.openclaw_client:
                reply = self.openclaw_client.chat(text)
            else:
                reply = self.engine.handle_user_text(text)
            self._update_status("replying")
            self._append_chat(f"OpenClaw: {reply}")
        except Exception as exc:
            reply = self.engine.handle_user_text(text)
            self._append_chat(f"[系统] OpenClaw请求失败，已回退本地回复: {exc}")
            self._append_chat(f"OpenClaw(本地): {reply}")

        self.voice.speak_async(reply, on_done=self._on_tts_done)

    def _on_tts_done(self) -> None:
        self.engine.after_reply()
        self.after(0, lambda: self._update_status(self.engine.state))


def run() -> None:
    app = OpenClawApp()
    app.mainloop()
