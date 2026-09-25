"""Behavioral verifier for sssdcache negative TTL invalidation replay."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

from reference_cache import filter_active_negatives, reference_replay, reference_snapshot

APP = Path("/app")
OPS = APP / "fixtures/ops"
CONFIG = APP / "config/sssdcache.json"
SNAPSHOT = APP / "state/sssd-cache-snapshot.json"
DB_PATH = APP / "state/sssd-cache.db"
OUTPUT = APP / "output/sssd-cache-report.json"
RESET = APP / "scripts/reset-state.sh"
HIDDEN_FIXTURES = Path("/tests/fixtures-hidden")
TB3_SAME_TS_SEQ = int(os.environ.get("TB3_SAME_TS_SEQ", "10"))
CLI = "/usr/local/bin/sssdcache"

FIXTURES = [
    "01-baseline.jsonl",
    "02-ttl-refresh.jsonl",
    "03-domain-keys.jsonl",
    "04-same-ts-order.jsonl",
    "05-nested-group.jsonl",
    "06-export-expired.jsonl",
    "07-lookup-hit.jsonl",
    "08-explicit-invalidate.jsonl",
]


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def reset_state() -> None:
    proc = _run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build_cli() -> None:
    proc = _run(["go", "build", "-mod=vendor", "-o", CLI, "./cmd/sssdcache"])
    assert proc.returncode == 0, proc.stderr


def ingest(
    ops: Path,
    snapshot: Path = SNAPSHOT,
    db: Path = DB_PATH,
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    return _run(
        [
            CLI,
            "ingest",
            "--ops",
            str(ops),
            "--config",
            str(CONFIG),
            "--snapshot",
            str(snapshot),
            "--db",
            str(db),
        ],
        env=env,
    )


def export_report(snapshot: Path = SNAPSHOT, output: Path = OUTPUT) -> subprocess.CompletedProcess[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    return _run([CLI, "export", "--snapshot", str(snapshot), "--output", str(output)])


class TestSSSDCacheReplay:
    """End-to-end sssdcache ingest/export against independent reference."""

    @classmethod
    def setup_class(cls) -> None:
        reset_state()
        build_cli()

    def test_public_fixtures_present(self) -> None:
        """Bundled JSONL operation logs must exist under /app/fixtures/ops/."""
        for name in FIXTURES:
            assert (OPS / name).is_file(), name

    def test_full_replay_matches_reference(self) -> None:
        """Cumulative replay export must match independent reference replay."""
        reset_state()
        proc = ingest(OPS)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        pub = export_report()
        assert pub.returncode == 0, pub.stderr or pub.stdout
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_replay(OPS, CONFIG)
        assert got == expect

    def test_staging_snapshot_written(self) -> None:
        """Ingest must write /app/state/sssd-cache-snapshot.json."""
        reset_state()
        proc = ingest(OPS)
        assert proc.returncode == 0, proc.stderr
        assert SNAPSHOT.is_file()
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        expect = reference_snapshot(OPS, CONFIG)
        assert snap == expect

    def test_canonical_artifact_paths_written(self) -> None:
        """Ingest and export must write /app/state/sssd-cache-snapshot.json, /app/state/sssd-cache.db, and /app/output/sssd-cache-report.json."""
        reset_state()
        proc = ingest(OPS)
        assert proc.returncode == 0, proc.stderr
        pub = export_report()
        assert pub.returncode == 0, pub.stderr
        assert SNAPSHOT == Path("/app/state/sssd-cache-snapshot.json")
        assert DB_PATH == Path("/app/state/sssd-cache.db")
        assert OUTPUT == Path("/app/output/sssd-cache-report.json")
        assert SNAPSHOT.is_file()
        assert DB_PATH.is_file()
        assert OUTPUT.is_file()
        json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        json.loads(OUTPUT.read_text(encoding="utf-8"))

    def test_wal_checkpoint_recorded(self) -> None:
        """Ingest must record wal_checkpoints after SQLite persist."""
        reset_state()
        proc = ingest(OPS)
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["stats"]["wal_checkpoints"] >= 1

    def test_negative_ttl_refresh_on_retry(self) -> None:
        """Repeat lookup_miss before expiry must refresh expires_at per negative-ttl-contract."""
        reset_state()
        proc = ingest(OPS / "02-ttl-refresh.jsonl")
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["stats"]["negative_refreshed"] >= 1
        neg = snap["negatives"][0]
        assert neg["expires_at"] == 23000

    def test_domain_scoped_name_keys(self) -> None:
        """Principals with the same name in different domains must not collide."""
        reset_state()
        proc = ingest(OPS / "03-domain-keys.jsonl")
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert len(snap["negatives"]) == 2
        pairs = {(n["domain"], n["name"]) for n in snap["negatives"]}
        assert pairs == {("Ex", "am"), ("E", "xam")}

    def test_same_timestamp_replay_order(self) -> None:
        """Equal ts and seq must apply lookup_miss before cache_put before cache_del."""
        reset_state()
        proc = ingest(OPS / "04-same-ts-order.jsonl")
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["negatives"] == []
        assert snap["positives"] == []

    def test_nested_group_invalidation(self) -> None:
        """Nested group membership changes must invalidate transitive users."""
        reset_state()
        proc = ingest(OPS / "05-nested-group.jsonl")
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["stats"]["group_invalidations"] >= 2
        names = {p["name"] for p in snap["positives"]}
        assert "alice" not in names

    def test_export_filters_expired_negatives(self) -> None:
        """Export active_negatives must exclude rows expired at evaluated_at_ms."""
        reset_state()
        proc = ingest(OPS / "06-export-expired.jsonl")
        assert proc.returncode == 0, proc.stderr
        export_report(output=APP / "output/expired-export.json")
        doc = json.loads((APP / "output/expired-export.json").read_text(encoding="utf-8"))
        names = {n["name"] for n in doc["active_negatives"]}
        assert "ghost" not in names
        assert "live" in names

    def test_sqlite_stores_active_negatives_only(self) -> None:
        """SQLite negative_cache must omit expired negatives at ingest time."""
        reset_state()
        proc = ingest(OPS / "06-export-expired.jsonl")
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute("SELECT name FROM negative_cache ORDER BY name").fetchall()
        finally:
            conn.close()
        active = filter_active_negatives(snap["negatives"], snap["evaluated_at_ms"])
        assert [r[0] for r in rows] == sorted(n["name"] for n in active)

    def test_publish_reads_snapshot_only(self) -> None:
        """Export must not re-read JSONL operation logs."""
        reset_state()
        ingest(OPS / "01-baseline.jsonl")
        before = SNAPSHOT.read_bytes()
        shutil.move(str(OPS), str(APP / "fixtures/ops.bak"))
        try:
            pub = export_report()
            assert pub.returncode == 0, pub.stderr
            assert SNAPSHOT.read_bytes() == before
        finally:
            shutil.move(str(APP / "fixtures/ops.bak"), str(OPS))

    def test_hidden_nested_churn(self) -> None:
        """Hidden nested churn fixture must match reference replay."""
        hidden = HIDDEN_FIXTURES / "08-nested-churn.jsonl"
        assert hidden.is_file(), "missing /tests/fixtures-hidden/08-nested-churn.jsonl"
        reset_state()
        proc = ingest(hidden)
        assert proc.returncode == 0, proc.stderr
        pub = export_report(output=APP / "output/hidden.json")
        assert pub.returncode == 0, pub.stderr
        got = json.loads((APP / "output/hidden.json").read_text(encoding="utf-8"))
        expect = reference_replay(hidden, CONFIG)
        assert got == expect
        assert got["stats"]["negative_refreshed"] >= 1
        assert got["stats"]["group_invalidations"] >= 1

    def test_tb3_same_ts_invalidate_lookup_hit_order(self) -> None:
        """TB3 same-ts bundle must honor invalidate before lookup_hit tie-break ordering."""
        trap = HIDDEN_FIXTURES / "09-tb3-same-ts-trap.jsonl"
        assert trap.is_file()
        reset_state()
        proc = ingest(trap)
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        expect = reference_snapshot(trap, CONFIG)
        assert snap["positives"] == expect["positives"]
        assert snap["negatives"] == expect["negatives"]
        assert snap["stats"]["explicit_invalidation"] == expect["stats"]["explicit_invalidation"]
        assert snap["stats"]["lookup_hit"] == expect["stats"]["lookup_hit"]
        assert TB3_SAME_TS_SEQ == 10

    def test_tb3_invalidate_poison_pill(self) -> None:
        """TB3 invalidate poison fixture must clear positive and negative rows."""
        poison = HIDDEN_FIXTURES / "10-tb3-invalidate-poison.jsonl"
        assert poison.is_file()
        reset_state()
        proc = ingest(poison)
        assert proc.returncode == 0, proc.stderr
        pub = export_report(output=APP / "output/tb3-poison.json")
        assert pub.returncode == 0, pub.stderr
        got = json.loads((APP / "output/tb3-poison.json").read_text(encoding="utf-8"))
        expect = reference_replay(poison, CONFIG)
        assert got == expect
        assert got["stats"]["explicit_invalidation"] >= 2
        assert got["positives"] == []
        assert got["active_negatives"] == []

    def test_domain_suffix_env_override(self) -> None:
        """SSSD_DOMAIN_SUFFIX must affect default domain for ops without domain field."""
        reset_state()
        proc = ingest(
            OPS / "01-baseline.jsonl",
            env={"SSSD_DOMAIN_SUFFIX": "corp.local"},
        )
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["domain_suffix"] == "corp.local"

    def test_lookup_hit_clears_negative(self) -> None:
        """lookup_hit must remove negative cache rows and increment lookup_hit stats."""
        reset_state()
        proc = ingest(OPS / "07-lookup-hit.jsonl")
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["stats"]["lookup_hit"] >= 1
        neg_names = {n["name"] for n in snap["negatives"]}
        assert "bob" not in neg_names
        expect = reference_snapshot(OPS / "07-lookup-hit.jsonl", CONFIG)
        assert snap["negatives"] == expect["negatives"]
        assert snap["stats"]["lookup_hit"] == expect["stats"]["lookup_hit"]

    def test_explicit_invalidate_clears_cache_rows(self) -> None:
        """Explicit invalidate must remove positive and negative rows for named principals."""
        reset_state()
        proc = ingest(OPS / "08-explicit-invalidate.jsonl")
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["stats"]["explicit_invalidation"] >= 2
        pos_names = {p["name"] for p in snap["positives"]}
        neg_names = {n["name"] for n in snap["negatives"]}
        assert "dana" not in pos_names
        assert "erin" not in neg_names
        expect = reference_snapshot(OPS / "08-explicit-invalidate.jsonl", CONFIG)
        assert snap["positives"] == expect["positives"]
        assert snap["negatives"] == expect["negatives"]
        assert snap["stats"]["explicit_invalidation"] == expect["stats"]["explicit_invalidation"]
