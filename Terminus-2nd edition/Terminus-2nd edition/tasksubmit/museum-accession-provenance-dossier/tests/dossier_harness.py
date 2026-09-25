"""CLI support helpers for musdoss tests."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
CLI_BIN = Path("/usr/local/bin/musdoss")
SNAP_PATH = APP_ROOT / "state" / "accession-vault.json"
DB_PATH = APP_ROOT / "work" / "register.db"
ARCHIVE_DIR = APP_ROOT / "fixtures" / "archives"
TRUSTED_DATA_DIR = Path("/tests/data")
TRUSTED_ARCHIVE_DIR = TRUSTED_DATA_DIR / "archives"
SEED_POOL = json.loads((TRUSTED_DATA_DIR / "seeds.json").read_text(encoding="utf-8"))["seeds"]


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=merged)


def load_json_nofollow(path: Path) -> dict:
    """Read a non-empty regular JSON file without following its final symlink."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        assert stat.S_ISREG(info.st_mode), f"graded output is not regular: {path}"
        assert info.st_size > 2, f"graded output is empty or a stub: {path}"
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = -1
            value = json.load(handle)
    finally:
        if fd >= 0:
            os.close(fd)
    assert isinstance(value, dict) and value, f"graded output is not a JSON object: {path}"
    return value


def reset_workspace() -> None:
    for root in (SNAP_PATH.parent, DB_PATH.parent, APP_ROOT / "output"):
        assert not root.is_symlink(), f"refusing symlinked workspace root: {root}"
        root.mkdir(parents=True, exist_ok=True)
        for child in root.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()


def emit_full_dossier(seed: str, archive: str, *, archive_dir: Path | None = None, env: dict | None = None) -> Path:
    merged = dict(env or {})
    if archive_dir is not None:
        merged["TB3_ARCHIVE_DIR"] = str(archive_dir)
    for step in (
        [str(CLI_BIN), "vault", "load", "--seed", seed, "--archive", archive],
        [str(CLI_BIN), "compose", "align", "--seed", seed, "--archive", archive],
    ):
        proc = invoke(step, env=merged)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    assert not SNAP_PATH.parent.is_symlink()
    assert SNAP_PATH.is_file() and not SNAP_PATH.is_symlink()
    assert not DB_PATH.parent.is_symlink()
    assert DB_PATH.is_file() and not DB_PATH.is_symlink()
    out = APP_ROOT / "output" / (seed + "-" + archive + "-dossier.json")
    proc = invoke(
        [str(CLI_BIN), "publish", "dossier", "--seed", seed, "--archive", archive, "--output", str(out)],
        env=merged,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert not out.parent.is_symlink()
    assert out.is_file() and not out.is_symlink()
    return out
