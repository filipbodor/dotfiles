import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        (self.home / ".zshrc").write_text("# previous shell\n")

    def run_restore(self, *args, answer=""):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/restore.py"), "--home", str(self.home), *args],
            input=answer, capture_output=True, text=True, timeout=10,
        )

    def test_preview_and_cancellation_do_not_modify_files(self):
        for args, answer in [((), ""), (("--apply",), "n\n")]:
            result = self.run_restore(*args, answer=answer)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("previous shell", result.stdout)
            self.assertEqual((self.home / ".zshrc").read_text(), "# previous shell\n")
            self.assertFalse((self.home / ".zprofile").exists())
            self.assertFalse((self.home / ".local").exists())

    def test_apply_preserves_original_and_private_overrides(self):
        (self.home / ".zshrc").chmod(0o640)
        for name in [".zshrc.local", ".gitconfig", ".npmrc"]:
            (self.home / name).write_text("LOCAL CONTENT\n")
        result = self.run_restore("--apply", answer="y\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list((self.home / ".local/state/dotfiles-backups").iterdir())
        self.assertEqual(len(backups), 1)
        backup = backups[0]
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
        self.assertEqual((backup / ".zshrc").stat().st_mode & 0o777, 0o600)
        self.assertEqual((backup / ".zshrc").read_text(), "# previous shell\n")
        self.assertEqual((self.home / ".zshrc").stat().st_mode & 0o777, 0o640)
        self.assertEqual((self.home / ".zshrc").read_bytes(), (ROOT / "shell/.zshrc").read_bytes())
        manifest = json.loads((backup / "manifest.json").read_text())
        self.assertFalse(next(item for item in manifest if item["path"] == ".zprofile")["existed"])
        for name in [".zshrc.local", ".gitconfig", ".npmrc"]:
            self.assertEqual((self.home / name).read_text(), "LOCAL CONTENT\n")
        second = self.run_restore("--apply", answer="y\n")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("Already up to date", second.stdout)
        self.assertEqual(len(list(backup.parent.iterdir())), 1)

    def test_symlink_is_refused_without_writing_any_files(self):
        external = self.home / "linked-shell"
        external.write_text("keep me\n")
        (self.home / ".zshrc").unlink()
        (self.home / ".zshrc").symlink_to(external)
        result = self.run_restore("--apply", answer="y\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(external.read_text(), "keep me\n")
        self.assertFalse((self.home / ".zprofile").exists())

    def test_editor_merge_preserves_unrelated_and_nested_settings(self):
        target = self.home / "Library/Application Support/Code/User/settings.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({
            "editor.fontSize": 17,
            "code-runner.executorMap": {"ruby": "ruby-custom", "python": "old-python"},
        }))
        result = self.run_restore("--vscode", "--apply", answer="y\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        settings = json.loads(target.read_text())
        self.assertEqual(settings["editor.fontSize"], 17)
        self.assertEqual(settings["code-runner.executorMap"]["ruby"], "ruby-custom")
        self.assertEqual(settings["code-runner.executorMap"]["python"], "python3 -u")

    def test_jsonc_is_refused_before_shell_installation(self):
        target = self.home / "Library/Application Support/Code/User/settings.json"
        target.parent.mkdir(parents=True)
        target.write_text('{ // comment\n "editor.fontSize": 17\n}\n')
        result = self.run_restore("--vscode", "--apply", answer="y\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("JSONC", result.stderr)
        self.assertEqual((self.home / ".zshrc").read_text(), "# previous shell\n")
        self.assertFalse((self.home / ".local").exists())


if __name__ == "__main__":
    unittest.main()
