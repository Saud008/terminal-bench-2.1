#!/usr/bin/env python3
"""Parse TRIVIAL/EASY platform summary from chat paste → jobs-local context JSON.

Used by hooks and trivial_easy_auto_finish.py — agents do not run this manually.

  python3 scripts/trivial_easy_context.py --save --slug <name> --text-file /tmp/paste.txt
  python3 scripts/trivial_easy_context.py --load --slug <name>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402


def context_path(slug: str) -> Path:
    return jobs_path(f"trivial-easy-context-{slug}.json")


def _parse_rate_from_line(line: str) -> str | None:
    """Return '4/5' style from '80% (4/5)' or '4/5 runs'."""
    m = re.search(r"\((\d+)\s*/\s*(\d+)\s*(?:runs?)?\)", line, re.I)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
    if m:
        return f"{m.group(1)}%"
    m = re.search(r"\b(\d+)\s*/\s*(\d+)\b", line)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return None


def parse_platform_summary(text: str) -> dict:
    """Extract difficulty, opus, gpt, status from platform paste."""
    out: dict = {
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "raw_snippet": text[:4000],
    }
    low = text.lower()
    if re.search(r"\bTRIVIAL\b", text):
        out["difficulty"] = "TRIVIAL"
    elif re.search(r"\bEASY\b", text, re.I):
        out["difficulty"] = "EASY"
    if re.search(r"\bunsolvable\b", low):
        out["status"] = "unsolvable"
    elif re.search(r"\bsolvable\b", low):
        out["status"] = "solvable"

    opus_line = ""
    gpt_line = ""
    for line in text.splitlines():
        ll = line.lower()
        if "opus" in ll or "claude-opus" in ll or "terminus-claude" in ll:
            opus_line = line
        if "gpt5" in ll or "gpt-5" in ll or "terminus-gpt" in ll:
            gpt_line = line

    if opus_line:
        r = _parse_rate_from_line(opus_line)
        if r:
            out["opus"] = r
    if gpt_line:
        r = _parse_rate_from_line(gpt_line)
        if r:
            out["gpt"] = r

    return out


def save_context(slug: str, text: str) -> Path | None:
    data = parse_platform_summary(text)
    if not data.get("opus") and not data.get("gpt") and not data.get("difficulty"):
        return None
    data["slug"] = slug
    path = jobs_path(f"trivial-easy-context-{slug}.json", mkdir=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # Sync platform scores → agent-smoke (blocks pack until --post-harden)
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from preupload_agent_calibration import sync_smoke_from_platform_context  # noqa: WPS433

        sync_smoke_from_platform_context(slug)
    except Exception:
        pass
    return path


def load_context(slug: str) -> dict | None:
    path = resolve_jobs_path(f"trivial-easy-context-{slug}.json")
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def is_trivial_easy_text(text: str) -> bool:
    if re.search(r"\bTRIVIAL\b", text):
        return True
    if re.search(r"\bEASY\b", text, re.I) and re.search(
        r"(opus|gpt|agent performance|unit tests)", text, re.I
    ):
        return True
    if re.search(r"\b[45]/5\b", text) and re.search(r"(opus|gpt|terminus-)", text, re.I):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--load", action="store_true")
    parser.add_argument("--text", default="")
    parser.add_argument("--text-file", type=Path, default=None)
    args = parser.parse_args()

    if args.save:
        text = args.text
        if args.text_file and args.text_file.is_file():
            text = args.text_file.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            print("ERROR: --save needs --text or --text-file", file=sys.stderr)
            return 1
        path = save_context(args.slug, text)
        if not path:
            print("WARN: no TRIVIAL/EASY fields parsed", file=sys.stderr)
            return 2
        print(path.relative_to(REPO_ROOT))
        return 0

    if args.load:
        data = load_context(args.slug)
        if not data:
            print("{}", end="")
            return 2
        print(json.dumps(data))
        return 0

    parser.error("use --save or --load")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
