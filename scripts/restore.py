#!/usr/bin/env python3
"""Preview shared shell settings; apply explicitly with private backups."""

import argparse
from datetime import datetime, timezone
import difflib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def write_atomic(path, content, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            os.fchmod(stream.fileno(), mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def plan(home, vscode):
    changes = []
    files = [(ROOT / "shell" / name, home / name)
             for name in (".zprofile", ".zshrc", ".profile")]
    if vscode:
        files.append((ROOT / "vscode/settings.json",
                      home / "Library/Application Support/Code/User/settings.json"))
    for source, target in files:
        if target.is_symlink():
            raise ValueError(f"Refusing to replace symlink: {target}; merge it manually.")
        before = target.read_bytes() if target.exists() else None
        after = source.read_bytes()
        if vscode and source.name == "settings.json" and before is not None:
            # Top-level preferences merge, preserving untracked language entries
            # and unrelated custom Code Runner overrides within objects.
            try:
                current = json.loads(before)
            except (ValueError, UnicodeDecodeError) as error:
                raise ValueError("VS Code settings use JSONC or invalid JSON; merge them manually.") from error
            if not isinstance(current, dict):
                raise ValueError("VS Code settings must be a JSON object.")
            for key, value in json.loads(after).items():
                if isinstance(value, dict) and isinstance(current.get(key), dict):
                    current[key].update(value)
                else:
                    current[key] = value
            after = (json.dumps(current, indent=2) + "\n").encode()
        if before != after:
            mode = stat.S_IMODE(target.stat().st_mode) if before is not None else 0o644
            changes.append((target, before, after, mode))
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="apply after showing diffs and confirming")
    parser.add_argument("--vscode", action="store_true", help="also merge VS Code preferences (macOS)")
    parser.add_argument("--home", type=Path, default=Path.home(), help="destination home directory")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    try:
        changes = plan(home, args.vscode)
        if not changes:
            print("Already up to date.")
            return 0
        for target, before, after, _ in changes:
            print("".join(difflib.unified_diff(
                (before or b"").decode().splitlines(keepends=True),
                after.decode().splitlines(keepends=True),
                fromfile=str(target), tofile=f"{target} (proposed)",
            )), end="")
        if not args.apply:
            print("Preview only. Use --apply to confirm and install these changes.")
            return 0
        if input("Back up and apply these changes? [y/N] ").strip().lower() != "y":
            print("Cancelled; no files changed.")
            return 0

        # Refuse to apply a preview that became stale while awaiting confirmation.
        for target, before, _, _ in changes:
            if target.is_symlink() or (target.read_bytes() if target.exists() else None) != before:
                raise ValueError(f"File changed during preview: {target}; run again.")
        backup_root = home / ".local/state/dotfiles-backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
        backup = Path(tempfile.mkdtemp(prefix=stamp, dir=backup_root))
        backup.chmod(0o700)
        manifest = []
        for target, before, _, mode in changes:
            relative = target.relative_to(home)
            manifest.append({"path": str(relative), "existed": before is not None, "mode": mode})
            if before is not None:
                saved = backup / relative
                write_atomic(saved, before, 0o600)
        write_atomic(backup / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode(), 0o600)
        print(f"Backup: {backup}", flush=True)
        # All originals are backed up before the first destination is replaced.
        for target, _, after, mode in changes:
            write_atomic(target, after, mode)
            print(f"Installed: {target}")
        print("Open a new terminal tab to load the shell settings.")
        return 0
    except (OSError, ValueError, EOFError) as error:
        print(f"Restore failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
