"""Install oracle module sources into /app."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

DEFAULT_MAP = {
    "statusmap_contract.go": "internal/grpc/statusmap.go",
    "trailer_guard.go": "internal/grpc/interceptors/trailer.go",
    "recv_limit_guard.go": "internal/grpc/interceptors/recv_limit.go",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files-root", type=Path, required=True)
    parser.add_argument("--app-root", type=Path, required=True)
    args = parser.parse_args()

    mapping = DEFAULT_MAP
    map_path = args.files_root / "module_map.json"
    if map_path.is_file():
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
