import os
from pathlib import Path
import tempfile
import unittest

from src.openclaw_app.launcher import default_openclaw_workdir, find_openclaw_executable


class LauncherTests(unittest.TestCase):
    def test_find_openclaw_in_programfiles(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "OpenClaw"
            base.mkdir(parents=True)
            exe = base / "openclaw.exe"
            exe.write_text("demo")

            old = os.environ.get("ProgramFiles")
            os.environ["ProgramFiles"] = td
            try:
                found = find_openclaw_executable()
                self.assertIsNotNone(found)
                self.assertTrue(found.endswith("openclaw.exe"))
            finally:
                if old is None:
                    del os.environ["ProgramFiles"]
                else:
                    os.environ["ProgramFiles"] = old

    def test_default_workdir_suffix(self):
        self.assertTrue(str(default_openclaw_workdir()).endswith('.openclaw'))


if __name__ == "__main__":
    unittest.main()
