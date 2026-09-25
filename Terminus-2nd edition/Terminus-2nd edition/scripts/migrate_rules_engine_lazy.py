#!/usr/bin/env python3
"""Migrate .cursor/rules/*.mdc to ENGINE_0 hub-only alwaysApply.

Hub (alwaysApply: true): LOCKED + ENGINE_0 files in terminus_engine_registry.HUB_RULES.
All other active rules: alwaysApply: false (lazy load per engine).
_legacy/, prompts/, tag-prompts/ stay false.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / ".cursor" / "rules"

sys.path.insert(0, str(REPO / "scripts"))
from terminus_engine_registry import HUB_RULES  # noqa: E402

HUB = set(HUB_RULES)


def rel(p: Path) -> str:
    return p.relative_to(RULES).as_posix()


def migrate() -> int:
    changed = 0
    for mdc in sorted(RULES.rglob("*.mdc")):
        r = rel(mdc)
        if r.startswith("_legacy/") or r.startswith("prompts/") or r.startswith("tag-prompts/"):
            want = False
        elif r in HUB:
            want = True
        else:
            want = False

        text = mdc.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        end = text.find("---", 3)
        if end < 0:
            continue
        fm = text[3:end]
        rest = text[end + 3 :]

        new_val = str(want).lower()
        if re.search(r"^alwaysApply:\s*", fm, re.M):
            new_fm = re.sub(
                r"^alwaysApply:\s*\w+",
                f"alwaysApply: {new_val}",
                fm,
                flags=re.M,
            )
        else:
            new_fm = fm.rstrip() + f"\nalwaysApply: {new_val}\n"

        new_text = "---" + new_fm + "---" + rest
        if new_text != text:
            mdc.write_text(new_text, encoding="utf-8")
            print(f"{'HUB' if want else 'lazy':5} {r}")
            changed += 1

    print(f"\nUpdated {changed} file(s). Hub count: {len(HUB)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(migrate())
