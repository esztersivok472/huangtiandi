from __future__ import annotations

import os
from pathlib import Path
import subprocess


def default_openclaw_workdir() -> Path:
    return Path.home() / ".openclaw"


def find_openclaw_executable() -> str | None:
    names = ["openclaw.exe", "openclaw-cli.exe", "openclaw.bat", "openclaw.cmd", "openclaw"]

    base_dirs = [
        default_openclaw_workdir(),
        default_openclaw_workdir() / "bin",
        Path.cwd(),
        Path.cwd() / "openclaw",
        Path.home() / "openclaw",
    ]

    for env_name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        env_val = os.environ.get(env_name)
        if env_val:
            base_dirs.append(Path(env_val) / "OpenClaw")
            base_dirs.append(Path(env_val))

    for base in base_dirs:
        for name in names:
            candidate = base / name
            if candidate.exists() and candidate.is_file():
                return str(candidate)

    return None


def start_openclaw(executable_path: str, workdir: str | None = None) -> subprocess.Popen:
    path = Path(executable_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"OpenClaw executable not found: {executable_path}")

    run_cwd = Path(workdir) if workdir else default_openclaw_workdir()
    if not run_cwd.exists():
        run_cwd = path.parent

    return subprocess.Popen([str(path)], cwd=str(run_cwd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
