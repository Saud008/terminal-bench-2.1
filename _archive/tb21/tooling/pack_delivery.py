#!/usr/bin/env python3
"""Final gate + zip for a TB 2.1 delivery (Master Ship Checklist 84, 85).

Runs master_check.py on <slug>/ (which includes tb21_check.py and
tb21_ship_check.py); refuses to pack unless every check 0-85 is PASS or
SIGNED against the current files. Writes READY_TO_SHIP/<slug>.zip containing exactly
<slug>/{<slug>/, rubric.txt, oracle-nop-evidence/, trajectories/} with no junk,
.sh files marked executable, then re-verifies the zip entries.

Usage:
    py -3 tb21/pack_delivery.py <slug-dir> [--out READY_TO_SHIP]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
JUNK_NAMES = {".DS_Store", "__MACOSX", ".git", "__pycache__", "SOURCE.txt", "Thumbs.db", ".pytest_cache", ".ruff_cache"}


def is_junk(rel: Path) -> bool:
    return any(part in JUNK_NAMES or part.startswith("._") for part in rel.parts) or rel.suffix == ".pyc"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug_dir")
    parser.add_argument("--out", default="READY_TO_SHIP")
    args = parser.parse_args()

    outer = Path(args.slug_dir).resolve()
    if outer.parent.name == outer.name:
        outer = outer.parent
    slug = outer.name

    proc = subprocess.run([sys.executable, str(HERE / "master_check.py"), str(outer)])
    if proc.returncode != 0:
        print("\nmaster_check.py is not green — not packing.")
        return 1

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{slug}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(outer.rglob("*")):
            rel = path.relative_to(outer)
            if not path.is_file() or is_junk(rel):
                continue
            info = zipfile.ZipInfo.from_file(path, arcname=f"{slug}/{rel.as_posix()}")
            mode = 0o755 if path.suffix == ".sh" else 0o644
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    bad = [n for n in names if is_junk(Path(n)) or not n.startswith(f"{slug}/")]
    tops = {n.split("/")[1] for n in names if n.count("/") >= 2 or n.split("/")[1]}
    expected = {slug, "rubric.txt", "oracle-nop-evidence", "trajectories"}
    if bad or tops != expected:
        print(f"zip verification failed: bad={bad[:5]} top-level={sorted(tops)}")
        return 1
    print(f"\npacked {zip_path} ({len(names)} files).")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
