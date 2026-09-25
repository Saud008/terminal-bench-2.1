"""Behavioral verifier for rspamd-fuzzy-audit checksum rotation pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from fuzzy_contract_math import (
    INDEX_PATH,
    ROLLBACK_PATH,
    RUN_PATH,
    SNAPSHOT_PATH,
    reference_rotate,
    reference_snapshot_with_env,
    shingle_hashes,
    normalize_body,
)

APP = Path("/app")
CLI = "/app/bin/rspamd-fuzzy-audit"
STATE_INDEX_PATH = "/app/state/fuzzy-index.db"
STATE_SNAPSHOT_PATH = "/app/state/shingle-snapshot.json"
STATE_RUN_PATH = "/app/state/rotation-run.json"
STATE_ROLLBACK_PATH = "/app/state/rotation-rollback.json"
FIXTURES = APP / "fixtures"
SCENARIOS = FIXTURES / "scenarios"
OUTPUT = APP / "output"
RESET = APP / "scripts" / "reset-state.sh"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
HIDDEN_ROOT = Path(os.environ.get("TB3_FIXTURES_DIR", "/opt/verifier-fixtures/rspamd-fuzzy"))

PROTECTED = [
    "fixtures/catalog.json",
    "docs/spec.md",
    "docs/shingle-window.md",
    "docs/key-epoch-rotation.md",
]


def _sha256(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


PROTECTED_SHA256 = {rel: _sha256(rel) for rel in PROTECTED}


def run(cmd: list[str], *, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    for script in (RESET, APP / "scripts" / "rebuild-rspamd-lib.sh", APP / "scripts" / "validate-lib.sh"):
        proc = run(["bash", str(script)])
        assert proc.returncode == 0, proc.stderr or proc.stdout


def scenario_dir(name: str, root: Path = SCENARIOS) -> Path:
    return root / name


def rotate_cli(
    name: str,
    *,
    root: Path = SCENARIOS,
    dry_run: bool = False,
    export_name: str | None = None,
    console_dump: Path | None = None,
    env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == name)
    sdir = scenario_dir(name, root)
    export = OUTPUT / (export_name or f"{name}.json")
    cmd = [
        CLI,
        "rotate",
        "--corpus-dir",
        str(sdir),
        "--key-manifest",
        str(sdir / entry["key_manifest"]),
        "--window-size",
        str(entry["window_size"]),
        "--console-dump",
        str(console_dump or (sdir / entry["console_dump"])),
        "--summary-out",
        str(export),
    ]
    if dry_run:
        cmd.append("--dry-run")
    return run(cmd, env=env)


def load_export(name: str, export_name: str | None = None) -> dict:
    return json.loads((OUTPUT / (export_name or f"{name}.json")).read_text(encoding="utf-8"))


def rotate_hidden(dirname: str, *, export_name: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    sdir = HIDDEN_ROOT / dirname
    meta = json.loads((sdir / "scenario.json").read_text(encoding="utf-8"))
    export = OUTPUT / export_name
    cmd = [
        CLI,
        "rotate",
        "--corpus-dir",
        str(sdir),
        "--key-manifest",
        str(sdir / "key-manifest.json"),
        "--window-size",
        str(meta["window_size"]),
        "--console-dump",
        str(sdir / "console.dump"),
        "--summary-out",
        str(export),
    ]
    return run(cmd, env=env)


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset()


@pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
def test_bundled_export_matches_reference(scenario_name: str) -> None:
    """Each catalog scenario export must match independent reference math."""
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == scenario_name)
    proc = rotate_cli(scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export(scenario_name)
    expect = reference_rotate(
        scenario_dir(scenario_name),
        entry["window_size"],
    )
    assert got == expect


def test_state_artifact_paths_match_contract() -> None:
    """State sqlite, rotation-run, and rollback paths match instruction contract."""
    assert str(INDEX_PATH) == STATE_INDEX_PATH
    assert str(SNAPSHOT_PATH) == STATE_SNAPSHOT_PATH
    assert str(RUN_PATH) == STATE_RUN_PATH
    assert str(ROLLBACK_PATH) == STATE_ROLLBACK_PATH


def test_shingle_snapshot_uses_manifest_order_only() -> None:
    """Shingle snapshot lists mails.tsv ids only, not every .eml on disk."""
    decoy = scenario_dir("basic-two-mails") / "decoy.eml"
    decoy.write_text("Subject: x\n\nignored\n", encoding="utf-8")
    try:
        proc = rotate_cli("basic-two-mails")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        expect = reference_snapshot_with_env(scenario_dir("basic-two-mails"))
        assert snap["mails"] == expect["mails"]
        assert snap["mail_digest"] == expect["mail_digest"]
        assert "decoy" not in snap["mails"]
    finally:
        decoy.unlink(missing_ok=True)


def test_overlap_unique_less_than_total_rows() -> None:
    """Duplicate shingles across mails must not inflate unique_shingles."""
    proc = rotate_cli("overlap-duplicates")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export("overlap-duplicates")
    assert doc["unique_shingles"] < doc["total_shingle_rows"]
    assert doc["total_shingle_rows"] > 10


def test_epoch_rotate_rehashes_seed_rows() -> None:
    """Seeded epoch-1 rows must rehash to epoch-2 algo-3 and verify against console."""
    proc = rotate_cli("epoch-rotate")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export("epoch-rotate")
    assert doc["key_epoch"] == 2
    assert doc["checksum_algo_id"] == 3
    conn = sqlite3.connect(INDEX_PATH)
    rows = conn.execute(
        "SELECT DISTINCT key_epoch, checksum_algo_id FROM fuzzy_hashes"
    ).fetchall()
    conn.close()
    assert rows == [(2, 3)]


def test_window_size_four_emits_expected_shingle_count() -> None:
    """Window 4 on alpha mail produces reference shingle cardinality."""
    proc = rotate_cli("basic-two-mails")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    alpha_body = normalize_body((scenario_dir("basic-two-mails") / "alpha.eml").read_text(encoding="utf-8"))
    expect_alpha = len(shingle_hashes(alpha_body, 4, 1, 1))
    conn = sqlite3.connect(INDEX_PATH)
    alpha_rows = conn.execute(
        "SELECT COUNT(*) FROM fuzzy_hashes WHERE mail_id='alpha'"
    ).fetchone()[0]
    conn.close()
    assert alpha_rows == expect_alpha


def test_dry_run_skips_index_and_rotation_run() -> None:
    """Dry-run must not write sqlite rows or rotation-run.json."""
    proc = rotate_cli("basic-two-mails", dry_run=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    if INDEX_PATH.exists():
        conn = sqlite3.connect(INDEX_PATH)
        count = conn.execute("SELECT COUNT(*) FROM fuzzy_hashes").fetchone()[0]
        conn.close()
        assert count == 0
    else:
        assert True
    assert not RUN_PATH.exists()
    doc = load_export("basic-two-mails")
    assert doc["dry_run"] is True
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == "basic-two-mails")
    expect = reference_rotate(
        scenario_dir("basic-two-mails"),
        entry["window_size"],
        dry_run=True,
    )
    assert doc == expect


def test_rotation_run_written_on_success() -> None:
    """Successful rotate writes rotation-run.json with export counters."""
    proc = rotate_cli("basic-two-mails")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert RUN_PATH.is_file()
    run_doc = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    export_doc = load_export("basic-two-mails")
    assert run_doc["unique_shingles"] == export_doc["unique_shingles"]
    assert run_doc["total_shingle_rows"] == export_doc["total_shingle_rows"]
    assert run_doc["console_lines_matched"] == export_doc["console_lines_matched"]


def test_console_lines_match_distinct_hashes() -> None:
    """console_lines_matched equals distinct hashes for active epoch."""
    proc = rotate_cli("basic-two-mails")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export("basic-two-mails")
    assert doc["console_lines_matched"] == doc["unique_shingles"]


def test_hidden_uppercase_console_dump() -> None:
    """Hidden /opt/verifier-fixtures/rspamd-fuzzy upper-console corpus."""
    hidden = Path("/opt/verifier-fixtures/rspamd-fuzzy") / "upper-console"
    meta = json.loads((hidden / "scenario.json").read_text(encoding="utf-8"))
    proc = rotate_hidden("upper-console", export_name="hidden-upper.json")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads((OUTPUT / "hidden-upper.json").read_text(encoding="utf-8"))
    expect = reference_rotate(hidden, meta["window_size"])
    assert got == expect


def test_hidden_near_duplicate_overlap() -> None:
    """Hidden /opt/verifier-fixtures/rspamd-fuzzy near-duplicate overlap corpus."""
    hidden = Path("/opt/verifier-fixtures/rspamd-fuzzy") / "near-duplicate"
    meta = json.loads((hidden / "scenario.json").read_text(encoding="utf-8"))
    proc = rotate_hidden("near-duplicate", export_name="hidden-near.json")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads((OUTPUT / "hidden-near.json").read_text(encoding="utf-8"))
    expect = reference_rotate(hidden, meta["window_size"])
    assert got == expect
    assert got["unique_shingles"] < got["total_shingle_rows"]


def test_hidden_epoch_salt_suffix_snapshot() -> None:
    """Hidden /opt/verifier-fixtures/rspamd-fuzzy salt-suffix snapshot corpus."""
    hidden = Path("/opt/verifier-fixtures/rspamd-fuzzy") / "salt-suffix"
    meta = json.loads((hidden / "scenario.json").read_text(encoding="utf-8"))
    suffix = meta["salt_suffix"]
    proc = rotate_hidden(
        "salt-suffix",
        export_name="hidden-salt.json",
        env={"RF_EPOCH_SALT_SUFFIX": suffix},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    key = json.loads((hidden / "key-manifest.json").read_text(encoding="utf-8"))
    assert snap["epoch_salt"] == key["epoch_salt"] + suffix


def test_anti_cheat_protected_files_unmodified() -> None:
    """Bundled contract files must remain unchanged."""
    for rel, digest in PROTECTED_SHA256.items():
        assert _sha256(rel) == digest, rel


def test_idempotent_second_rotate_same_export() -> None:
    """Second rotate on unchanged corpus reproduces export counters."""
    proc1 = rotate_cli("basic-two-mails", export_name="first.json")
    assert proc1.returncode == 0, proc1.stderr or proc1.stdout
    first = load_export("basic-two-mails", export_name="first.json")
    proc2 = rotate_cli("basic-two-mails", export_name="second.json")
    assert proc2.returncode == 0, proc2.stderr or proc2.stdout
    second = load_export("basic-two-mails", export_name="second.json")
    assert first["unique_shingles"] == second["unique_shingles"]
    assert first["total_shingle_rows"] == second["total_shingle_rows"]


def test_no_rollback_marker_on_success() -> None:
    """Successful rotation must not leave a rollback marker file."""
    proc = rotate_cli("basic-two-mails")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert not ROLLBACK_PATH.exists()


def test_console_mismatch_writes_rollback_marker() -> None:
    """Failed console verify must write rotation-rollback.json and exit non-zero."""
    sdir = scenario_dir("basic-two-mails")
    key = json.loads((sdir / "key-manifest.json").read_text(encoding="utf-8"))
    bad_dump = OUTPUT / "bad-console.dump"
    bad_dump.write_text("hash=deadbeefdeadbeef epoch=1 algo=1\n", encoding="utf-8")
    proc = rotate_cli(
        "basic-two-mails",
        export_name="rollback-fail.json",
        console_dump=bad_dump,
    )
    assert proc.returncode != 0, proc.stdout or proc.stderr
    assert ROLLBACK_PATH.is_file(), "rotation-rollback.json missing after console mismatch"
    rollback = json.loads(ROLLBACK_PATH.read_text(encoding="utf-8"))
    assert rollback == {
        "schema": 1,
        "key_epoch": key["key_epoch"],
        "checksum_algo_id": key["checksum_algo_id"],
        "reason": "console_mismatch",
    }


def test_beta_mail_contributes_distinct_shingles() -> None:
    """Second bundled mail adds hashes beyond alpha-only baseline."""
    proc = rotate_cli("basic-two-mails")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    conn = sqlite3.connect(INDEX_PATH)
    beta = conn.execute("SELECT COUNT(*) FROM fuzzy_hashes WHERE mail_id='beta'").fetchone()[0]
    alpha = conn.execute("SELECT COUNT(*) FROM fuzzy_hashes WHERE mail_id='alpha'").fetchone()[0]
    conn.close()
    assert beta > 0
    assert alpha > 0


def test_dry_run_unique_shingles_uses_distinct_hash_semantics() -> None:
    """Dry-run summary unique_shingles must match reference distinct-hash math."""
    proc = rotate_cli("overlap-duplicates", dry_run=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export("overlap-duplicates")
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == "overlap-duplicates")
    expect = reference_rotate(
        scenario_dir("overlap-duplicates"),
        entry["window_size"],
        dry_run=True,
    )
    assert doc["unique_shingles"] == expect["unique_shingles"]
    assert doc["unique_shingles"] < doc["total_shingle_rows"]


def test_corpus_ingest_manifest_order_matches_reference() -> None:
    """Corpus manifest sequence via mails.tsv matches shingle snapshot reference."""
    proc = rotate_cli("epoch-rotate")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    expect = reference_snapshot_with_env(scenario_dir("epoch-rotate"))
    assert snap["mails"] == expect["mails"]
