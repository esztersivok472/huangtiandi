from pathlib import Path
import tempfile
import unittest

from src.openclaw_app.core import ConversationEngine


class ConversationEngineTests(unittest.TestCase):
    def test_start_and_end_call(self):
        engine = ConversationEngine()
        self.assertEqual(engine.state, "idle")

        engine.start_call()
        self.assertEqual(engine.state, "listening")

        engine.end_call()
        self.assertEqual(engine.state, "idle")

    def test_handle_user_text_changes_state_and_history(self):
        engine = ConversationEngine()
        engine.start_call()

        reply = engine.handle_user_text("你好")
        self.assertIn("你好", reply)
        self.assertEqual(engine.state, "replying")
        self.assertEqual(len(engine.history), 2)
        self.assertEqual(engine.history[0].role, "user")
        self.assertEqual(engine.history[1].role, "assistant")

        engine.after_reply()
        self.assertEqual(engine.state, "listening")


    def test_apply_reference_avatar_preset(self):
        engine = ConversationEngine()
        avatar = engine.apply_reference_avatar_preset()
        self.assertEqual(avatar.name, "霓虹潮流女孩")
        self.assertEqual(avatar.model_id, "preset_neon_girl_v1")
        self.assertEqual(avatar.avatar_type, "generated")

    def test_set_avatar_image(self):
        engine = ConversationEngine()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp = Path(f.name)
            temp.write_bytes(b"img")

        try:
            engine.set_avatar_image(str(temp))
            self.assertEqual(engine.avatar.image_path, str(temp))
        finally:
            temp.unlink(missing_ok=True)

    def test_generate_avatar_from_image(self):
        engine = ConversationEngine()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp = Path(f.name)
            temp.write_bytes(b"avatar-bytes")

        try:
            avatar = engine.generate_avatar_from_image(str(temp))
            self.assertEqual(avatar.avatar_type, "generated")
            self.assertTrue(avatar.model_id.startswith("mdl_"))
            self.assertEqual(avatar.style, "上传生成")
        finally:
            temp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
