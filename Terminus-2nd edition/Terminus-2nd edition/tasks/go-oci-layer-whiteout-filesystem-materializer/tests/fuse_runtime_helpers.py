"""layerfuse runtime helpers for atlas verifier tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

FUSE_BIN = Path("/usr/local/bin/layerfuse")
VAR_ROOT = Path("/app/var/layerfuse")
OUT_ROOT = Path("/app/output")

MEMBER_LEDGER = VAR_ROOT / "tar-member-ledger.json"
INGEST_COUNTER = VAR_ROOT / "ingest-counter.json"
OVERLAY_VIEW = VAR_ROOT / "overlay-merge.json"
ATLAS_OUT = OUT_ROOT / "filesystem-atlas.json"
BUNDLED_STACK = Path("/app/fixtures/oci-stacks/stack.json")
HIDDEN_STACK_ROOT = Path("/opt/verifier-fixtures/oci-layers")


def fuse_run(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(FUSE_BIN), *argv],
        capture_output=True,
        text=True,
        check=False,
    )


def fuse_run_ok(*argv: str) -> None:
    proc = fuse_run(*argv)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"layerfuse failed: {argv}")


def load_json_doc(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def wipe_fuse_state() -> None:
    for path in (MEMBER_LEDGER, INGEST_COUNTER, OVERLAY_VIEW, ATLAS_OUT):
        if path.exists():
            path.unlink()


def fuse_publish_all(stack_json: Path) -> None:
    wipe_fuse_state()
    fuse_run_ok("ingest", str(stack_json))
    fuse_run_ok("materialize")
    fuse_run_ok("manifest", "export")
