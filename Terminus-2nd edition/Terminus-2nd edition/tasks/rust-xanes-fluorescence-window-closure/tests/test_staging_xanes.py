"""Staging snapshot traps for broken xanes modules under /opt/verifier-broken-xanes."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

APP = Path("/app")
CORE = APP / "crates/xanes-core/src"
BROKEN_ROOT = Path("/opt/verifier-broken-xanes")
ORACLE = Path("/tests/golden_modules")
MODULES = ("victoreen_fit", "edge_ordinal", "mu_window_seal")
ORACLE_MAP = {
    "victoreen_fit": "oracle_victoreen_fit.rs",
    "edge_ordinal": "oracle_edge_ordinal.rs",
    "mu_window_seal": "oracle_mu_window_seal.rs",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def rebuild() -> None:
    proc = run(
        [
            "bash",
            "-lc",
            "cargo build --locked --release --bin xanesctl && install -m 0755 target/release/xanesctl /usr/local/bin/xanesctl",
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_broken_staging_snapshot_paths_exist() -> None:
    """Broken module staging snapshots must live under /opt/verifier-broken-xanes."""
    for mod in MODULES:
        snap = BROKEN_ROOT / f"{mod}.rs"
        assert snap.is_file(), f"missing staging snapshot {snap}"


def test_victoreen_staging_snapshot_differs_from_oracle() -> None:
    """Staging victoreen_fit.rs must differ from oracle victoreen on disk."""
    broken = (BROKEN_ROOT / "victoreen_fit.rs").read_text(encoding="utf-8")
    golden = (ORACLE / ORACLE_MAP["victoreen_fit"]).read_text(encoding="utf-8")
    assert broken != golden


def test_edge_ordinal_staging_snapshot_differs_from_oracle() -> None:
    """Staging edge_ordinal.rs must differ from oracle edge ordinal table."""
    broken = (BROKEN_ROOT / "edge_ordinal.rs").read_text(encoding="utf-8")
    golden = (ORACLE / ORACLE_MAP["edge_ordinal"]).read_text(encoding="utf-8")
    assert broken != golden


def test_mu_window_seal_staging_snapshot_differs_from_oracle() -> None:
    """Staging mu_window_seal.rs must differ from oracle seal export path."""
    broken = (BROKEN_ROOT / "mu_window_seal.rs").read_text(encoding="utf-8")
    golden = (ORACLE / ORACLE_MAP["mu_window_seal"]).read_text(encoding="utf-8")
    assert broken != golden


def test_restore_staging_snapshot_roundtrip() -> None:
    """Copy staging snapshot back to /app and rebuild without error."""
    # Snapshot current /app modules so this trap does not leave golden sources installed.
    backup = {mod: (CORE / f"{mod}.rs").read_bytes() for mod in MODULES}
    try:
        for mod in MODULES:
            shutil.copy2(BROKEN_ROOT / f"{mod}.rs", CORE / f"{mod}.rs")
        rebuild()
    finally:
        for mod in MODULES:
            (CORE / f"{mod}.rs").write_bytes(backup[mod])
        rebuild()
