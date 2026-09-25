#!/usr/bin/env python3
"""Install repaired demo-index shell modules into /app/lib."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files-root", type=Path, required=True)
    parser.add_argument("--app-root", type=Path, required=True)
    args = parser.parse_args()

    map_path = args.files_root / "module_map.json"
    if not map_path.is_file():
        raise SystemExit(f"oracle: missing {map_path}")
    mapping = json.loads(map_path.read_text(encoding="utf-8"))

    for src_name, dest_rel in mapping.items():
        src = args.files_root / src_name
        dest = args.app_root / dest_rel
        if not src.is_file():
            raise SystemExit(f"oracle: missing {src}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


if __name__ == "__main__":
    main()
