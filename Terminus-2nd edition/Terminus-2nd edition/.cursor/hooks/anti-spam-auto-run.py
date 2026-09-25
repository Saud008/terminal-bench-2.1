#!/usr/bin/env python3
"""Cursor hook — auto-run anti-spam on task file writes (postToolUse / afterFileEdit)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from anti_spam_hook_runner import extract_written_path, handle_file_event  # noqa: E402


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({}))
        return 0

    path = extract_written_path(data)
    if not path:
        print(json.dumps({}))
        return 0

    _code, ctx = handle_file_event(path)
    if ctx:
        print(json.dumps({"additional_context": ctx}))
    else:
        print(json.dumps({}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
