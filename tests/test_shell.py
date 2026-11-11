import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPILER = shutil.which("g++-15")


@unittest.skipUnless(COMPILER and shutil.which("zsh"), "requires Zsh and GCC 15")
class RuncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)
        tools = self.cwd / "bin"
        tools.mkdir()
        compiler = tools / "g++-15"
        compiler.write_text(f'#!/bin/sh\nexec {shlex.quote(COMPILER)} "$@"\n')
        compiler.chmod(0o755)
        self.env = {
            **os.environ,
            "HOME": str(self.cwd),
            "ZSH": str(self.cwd / "no-oh-my-zsh"),
            "PATH": f"{tools}:/usr/bin:/bin",
        }
        (self.cwd / "sample with spaces.cpp").write_text(
            '#include <iostream>\nint main() { int n = 0; std::cin >> n; '
            'std::cout << n + 1 << "\\n"; }\n'
        )

    def run_runc(self, *args, stdin=""):
        return subprocess.run(
            ["/bin/zsh", "-f", "-c", 'source "$1"; shift; runc "$@"',
             "zsh", str(ROOT / "shell/.zshrc"), *args],
            cwd=self.cwd, env=self.env, input=stdin, capture_output=True,
            text=True, timeout=30,
        )

    def test_explicit_input_overrides_default_and_handles_spaces(self):
        (self.cwd / "in.txt").write_text("10\n")
        (self.cwd / "other input.txt").write_text("41\n")
        result = self.run_runc("sample with spaces.cpp", "other input.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "42\n")

    def test_default_input_and_terminal_fallback(self):
        (self.cwd / "in.txt").write_text("9\n")
        result = self.run_runc("sample with spaces")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "10\n")
        (self.cwd / "in.txt").unlink()
        result = self.run_runc("sample with spaces", stdin="20\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "21\n")

    def test_missing_input_does_not_rebuild_and_compile_error_does_not_run(self):
        executable = self.cwd / "sample with spaces"
        executable.write_text("#!/bin/sh\necho STALE\n")
        executable.chmod(0o755)
        result = self.run_runc("sample with spaces", "missing.txt")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Input file", result.stderr)
        self.assertIn("STALE", executable.read_text())
        (self.cwd / "sample with spaces.cpp").write_text("invalid C++\n")
        result = self.run_runc("sample with spaces")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("STALE", result.stdout)


if __name__ == "__main__":
    unittest.main()
