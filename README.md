# huangtiandi

## OpenClaw 可执行 Demo（本地版）

这是一个可直接运行的程序（不是纯文档），包含：

- 可见人物形象（支持上传头像图片）
- 人物风格选择（商务/动漫/科幻/写实/可爱）
- 图片生成人物（MVP：从上传图片生成可追踪人物ID）
- 电话式对话状态（idle/listening/thinking/replying）
- 文字输入对话 + 本地语音播报（TTS，支持打断）
- 麦克风语音输入（STT，可选依赖）
- OpenClaw 自动连接（支持本地服务自动发现）
- 连续语音（更接近电话式持续对话）

> 说明：当前是可运行 MVP，用于先验证流程、功能与稳定性；后续可替换为真实云端 STT/LLM/TTS。

---


## 0) 你要的一键方式（Windows）

如果你不想手动配环境，直接双击：

- `one_click_install_and_run.bat`

这个脚本会自动：
1. 检查 Python 是否已安装
2. 创建 `.venv`
3. 安装依赖
4. 启动程序

## 1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 可选：麦克风语音识别依赖

如果你要用 `🎤语音输入`，通常还需要系统音频依赖（如 PyAudio）。

- Windows（常见）：
  ```bash
  pip install pipwin
  pipwin install pyaudio
  ```

---

## 2) 启动程序

```bash
python main.py
```

---

## 3) 运行测试（先测再打包）

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m py_compile main.py src/openclaw_app/core.py src/openclaw_app/gui.py tests/test_core.py
```

---

## 4) 打包为可执行文件

### Windows 打包为 .exe

在 Windows 环境中执行：

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name openclaw_demo main.py
```

输出文件：

- `dist/openclaw_demo.exe`

### Linux/macOS

同样命令可生成对应平台可执行文件（不是 `.exe`）。

---

## 5) 目录结构

```text
main.py
src/openclaw_app/core.py
src/openclaw_app/gui.py
src/openclaw_app/voice.py
tests/test_core.py
requirements.txt
```


## 6) 生成可安装的 Windows 安装包（.exe）

我已经把打包脚本放到仓库里了，你在 Windows 电脑上执行即可：

1. 双击或在终端运行：
   - `scripts\build_windows.bat`（cmd，一键构建并在检测到 Inno Setup 时自动产出安装包）
   - `scripts\build_windows.ps1`（PowerShell）
2. 这一步会生成：
   - `dist/openclaw_demo.exe`（程序本体）
   - `installer/payload/*`（安装包素材）
3. 如果本机已安装 Inno Setup，会自动生成：
   - `installer/output/openclaw_demo_setup.exe`
4. 如果未安装 Inno Setup，脚本会提示你安装后再执行命令。

### 运行体验前建议先做的检查

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python main.py
```

如果你希望，我下一步可以继续给你加：
- 自动升级检测
- 程序图标、安装卸载 Logo
- 安装后首次运行环境自检（麦克风、语音依赖、网络）


## 7) 常见问题（你遇到的两个重点）

### A. 点了“语音输入”没反应

新版已改成后台线程识别，不会卡住界面；识别失败会在聊天窗口显示具体错误原因。

请先检查：
1. 已点击“开始通话”
2. Windows 麦克风权限已允许该程序
3. 如果 Google 识别失败，会自动尝试 Sphinx 离线识别（若本机已安装）

### B. 没有连到 OpenClaw

新版会启动后自动检测常见地址：
- `http://127.0.0.1:3000`
- `http://localhost:3000`
- 以及常见开发端口（5173/8000/8080/11434）

你也可以手动在界面“OpenClaw地址”里填地址，点“连接测试”。
连接失败会自动回退本地离线回复，不会中断对话。

### C. 人物形象空白

新版加入了默认可见头像（Canvas 绘制），即使没上传图片也能看到人物；
上传 PNG 会显示图片，非 PNG 会保留默认头像并显示文件名提示。


### D. 如何像打电话一样持续对话

1. 点击“开始通话”
2. 勾选“连续语音”
3. 点击“开始连续听说”
4. 结束时点击“结束通话”

程序会循环监听麦克风并自动发送到 OpenClaw（连接成功时）或本地回退引擎（连接失败时）。
