#!/usr/bin/env python3
"""Measure fresh login shell startup against Zsh without startup files."""

import argparse
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=5, help="measured runs per shell (1–30)")
    args = parser.parse_args()
    if not 1 <= args.runs <= 30:
        parser.error("--runs must be between 1 and 30")
    zsh = shutil.which("zsh")
    if not zsh:
        parser.error("zsh is not installed")

    # Avoid carrying a parent shell's Node manager selection into a fresh shell.
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("FNM_", "NVM_"))}
    env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
    env.setdefault("TERM", "xterm-256color")
    modes = [
        ("Minimal Zsh", [zsh, "-d", "-f", "-l", "-i", "-c", "exit"]),
        ("Configured login shell", [zsh, "-l", "-i", "-c", "exit"]),
    ]
    for label, command in modes:
        durations = []
        # One warm-up run so completion-cache creation does not dominate the median.
        for index in range(args.runs + 1):
            started = time.perf_counter()
            try:
                result = subprocess.run(
                    command, cwd=Path.home(), env=env, stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE, text=True, timeout=30,
                )
            except subprocess.TimeoutExpired:
                print(f"{label}: startup exceeded 30 seconds.", file=sys.stderr)
                return 1
            elapsed = time.perf_counter() - started
            if result.returncode:
                print(f"{label} failed ({result.returncode}): {result.stderr.strip()}", file=sys.stderr)
                return 1
            if index:
                durations.append(elapsed * 1000)
        print(f"{label}: median {statistics.median(durations):.1f} ms "
              f"(min {min(durations):.1f}, max {max(durations):.1f}; {args.runs} runs)",
              flush=True)
    print("Measured in your home directory; includes local overrides. "
          "This is startup timing, not prompt redraw or terminal rendering.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
