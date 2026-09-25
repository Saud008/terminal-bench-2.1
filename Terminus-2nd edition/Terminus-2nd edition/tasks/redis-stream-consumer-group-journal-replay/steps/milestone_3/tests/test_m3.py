"""Milestone 3 — export rollup pel distinct count and idempotent reclaim totals."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

CLI = "/app/bin/redisctl"
STAGE = Path("/app/state/redis-stream-stage.json")
ROLLUP = Path("/app/output/stream-rollup.json")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return sorted(rows, key=lambda r: r["seq"])


def reference_pel_distinct(stage: dict[str, Any], stream: str, group: str) -> int:
    grp = stage["streams"][stream]["groups"][group]
    return len(grp["pending"])


def reference_reclaim_total(stage: dict[str, Any], stream: str, group: str) -> int:
    return stage["streams"][stream]["groups"][group]["reclaim_total"]


def run_replay(journal: Path) -> None:
    if STAGE.exists():
        STAGE.unlink()
    if ROLLUP.exists():
        ROLLUP.unlink()
    proc = subprocess.run([CLI, "replay", str(journal)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def run_export(pass_no: int = 1) -> dict[str, Any]:
    proc = subprocess.run(
        [CLI, "export", "--pass", str(pass_no)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(ROLLUP.read_text(encoding="utf-8"))


class TestMilestone3:
    """Export rollup distinct PEL and idempotent second pass."""

    def test_export_writes_rollup_file(self) -> None:
        """export must create /app/output/stream-rollup.json."""
        run_replay(Path("/app/data/m3_reclaim_export.jsonl"))
        rollup = run_export(1)
        assert ROLLUP.is_file()
        assert "groups" in rollup

    def test_pel_distinct_not_delivery_sum(self) -> None:
        """pel_distinct counts distinct ids despite delivery_count > 1."""
        run_replay(Path("/app/data/m3_reclaim_export.jsonl"))
        stage = json.loads(STAGE.read_text(encoding="utf-8"))
        rollup = run_export(1)
        row = next(g for g in rollup["groups"] if g["group"] == "g1")
        assert row["pel_distinct"] == reference_pel_distinct(stage, "ledger", "g1")
        assert row["pel_distinct"] == 1

    def test_reclaim_total_matches_stage(self) -> None:
        """reclaim_total mirrors stage reclaim counter."""
        run_replay(Path("/app/data/m3_reclaim_export.jsonl"))
        stage = json.loads(STAGE.read_text(encoding="utf-8"))
        rollup = run_export(1)
        row = next(g for g in rollup["groups"] if g["group"] == "g1")
        assert row["reclaim_total"] == reference_reclaim_total(stage, "ledger", "g1")

    def test_second_export_pass_idempotent_reclaim(self) -> None:
        """Second export pass must not double reclaim_total."""
        run_replay(Path("/app/data/m3_reclaim_export.jsonl"))
        first = run_export(1)
        second = run_export(2)
        g1_first = next(g for g in first["groups"] if g["group"] == "g1")
        g1_second = next(g for g in second["groups"] if g["group"] == "g1")
        assert g1_second["reclaim_total"] == g1_first["reclaim_total"]

    def test_reopen_stage_between_exports(self) -> None:
        """Re-read persisted stage between export passes stays stable."""
        run_replay(Path("/app/data/m3_reclaim_export.jsonl"))
        run_export(1)
        stage_bytes = STAGE.read_bytes()
        run_export(2)
        assert STAGE.read_bytes() == stage_bytes

    def test_subprocess_export_cli(self) -> None:
        """export runs through subprocess on rebuilt binary."""
        run_replay(Path("/app/data/m3_reclaim_export.jsonl"))
        proc = subprocess.run([CLI, "export"], capture_output=True, text=True)
        assert proc.returncode == 0

    def test_stream_lengths_in_rollup(self) -> None:
        """rollup includes stream_lengths map."""
        run_replay(Path("/app/data/m3_reclaim_export.jsonl"))
        rollup = run_export(1)
        assert rollup["stream_lengths"]["ledger"] == 1

    def test_tb3_hidden_reexport_idempotency(self) -> None:
        """Hidden TB3 journal keeps reclaim idempotent on pass two."""
        base = _load_jsonl(Path("/app/data/m3_reclaim_export.jsonl"))
        for ev in base:
            ev["stream"] = "tb3_" + ev["stream"]
        tmp = Path("/tmp/tb3_m3.jsonl")
        tmp.write_text("\n".join(json.dumps(e) for e in base) + "\n", encoding="utf-8")
        run_replay(tmp)
        a = run_export(1)
        b = run_export(2)
        key = "tb3_ledger"
        ga = next(g for g in a["groups"] if g["stream"] == key)
        gb = next(g for g in b["groups"] if g["stream"] == key)
        assert gb["reclaim_total"] == ga["reclaim_total"]
