"""G-026 pytest entrypoint — suite uses interval_checker.reference_ledger."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

for _sub in ("harness", "yard_math", ""):
    _p = f"/app/scripts/{_sub}" if _sub else "/app/scripts"
    if _p not in sys.path:
        sys.path.insert(0, _p)

from interval_checker import reference_ledger  # noqa: F401


def test_t56c237_r7k2_railpos_binary_installed():
    """railpos must be installed at /app/bin/railpos per instruction."""
    assert Path("/app/bin/railpos").exists()


def test_t56c237_r7k2_railpos_cli_requires_subcommand():
    """railpos must reject invocations without a subcommand."""
    proc = subprocess.run(["/app/bin/railpos"], capture_output=True, text=True, check=False)
    assert proc.returncode != 0


def test_t56c237_r7k2_compile_trackgraph_writes_topo_persist_and_ticket():
    """compile-trackgraph must write zone snapshot cache and authority-ticket.json."""
    from railpos_cli_paths import CLI_BIN, GEN_PATH, SEED_POOL, SNAP_PATH, wipe

    wipe()
    seed = SEED_POOL[0]
    proc = subprocess.run(
        [str(CLI_BIN), "compile-trackgraph", "--seed", seed, "--scenario", "linear-chain"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert SNAP_PATH.exists()
    snap = __import__("json").loads(SNAP_PATH.read_text(encoding="utf-8"))
    assert snap["load_seq"] >= 1
    assert snap["scenario"] == "linear-chain"
    assert "blk-a7" in snap["zone_map"]
    assert GEN_PATH.exists()
    gen = __import__("json").loads(GEN_PATH.read_text(encoding="utf-8"))
    assert gen["possession_id"].startswith("poss-")
    assert gen["active"] is True


def test_t56c237_r7k2_topo_persist_increments_on_second_compile():
    """Second compile-trackgraph for same seed must increment load_seq."""
    from railpos_cli_paths import CLI_BIN, SEED_POOL, SNAP_PATH, wipe

    wipe()
    seed = SEED_POOL[1]
    subprocess.run(
        [str(CLI_BIN), "compile-trackgraph", "--seed", seed, "--scenario", "linear-chain"],
        check=True,
    )
    first = __import__("json").loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    subprocess.run(
        [str(CLI_BIN), "compile-trackgraph", "--seed", seed, "--scenario", "diamond-fork"],
        check=True,
    )
    second = __import__("json").loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    assert second == first + 1


def test_t56c237_r7k2_emit_honors_output_root():
    """emit-conflicts writes caller reports under /app/output/."""
    from railpos_cli_paths import OUTPUT_DIR, SEED_POOL, run_pipeline

    out = run_pipeline(SEED_POOL[0], "linear-chain")
    assert str(out).startswith(OUTPUT_DIR)
