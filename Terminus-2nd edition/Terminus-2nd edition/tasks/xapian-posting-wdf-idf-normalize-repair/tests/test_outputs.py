"""Behavioral verifier for Xapian posting WDF-IDF normalize repair."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_xapian_weight import pipeline_reference

APP = Path("/app")
CLI = Path("/usr/local/bin/xapian-weight-cli")
INDEX = APP / "work" / "index.json"
OUTPUT = APP / "output"
STAGING = APP / "state" / "index-staging.json"
BATCHES = APP / "fixtures" / "documents"
HIDDEN = Path("/opt/verifier-fixtures/documents")

CATALOG = [
    ("tech-rust.jsonl", "rust AND memory"),
    ("dup-collapse.jsonl", "alpha OR beta"),
    ("or-rare.jsonl", "uniqueterm OR wolf"),
]

PATCH_TARGETS = {
    "collector": APP / "crates/xapi-wdf/src/collector.rs",
    "cf_table": APP / "crates/xapi-index/src/cf_table.rs",
    "norm": APP / "crates/xapi-length/src/norm.rs",
    "expand": APP / "crates/xapi-synonym/src/expand.rs",
    "or_branch": APP / "crates/query-planner/src/or_branch.rs",
    "store": APP / "crates/ingest-stage/src/store.rs",
}

PROTECTED_RELS = (
    "config/weight.json",
    "docs/xapian-weight.md",
    "docs/token-collapse.md",
    "docs/synonym-policy.md",
    "docs/query-planner.md",
    "docs/staging-snapshot.md",
    "docs/repair-scope.md",
    "fixtures/catalog.json",
    "fixtures/documents/tech-rust.jsonl",
    "fixtures/documents/dup-collapse.jsonl",
    "fixtures/documents/or-rare.jsonl",
    "crates/xapian-weight-cli/src/main.rs",
    "crates/xapi-types/src/document.rs",
    "crates/xapi-types/src/index.rs",
    "crates/xapi-types/src/query.rs",
    "crates/xapi-tokenize/src/lib.rs",
    "crates/xapi-index/src/posting_merge.rs",
    "crates/xapi-weight/src/idf_table.rs",
    "crates/query-planner/src/parse.rs",
    "crates/ingest-stage/src/parse.rs",
    "crates/ingest-stage/src/staging.rs",
    "scripts/reset-state.sh",
    "scripts/rebuild.sh",
)

PROTECTED_SHA256: dict[str, str] = {
    rel: hashlib.sha256((APP / rel).read_bytes()).hexdigest()
    for rel in PROTECTED_RELS
    if (APP / rel).is_file()
}


def _build() -> None:
    proc = subprocess.run(
        ["bash", "/app/scripts/rebuild.sh"],
        cwd=APP,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _reset() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def _run(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [str(CLI), *args],
        cwd=APP,
        capture_output=True,
        text=True,
        env=merged,
    )


def _index(batch: Path) -> subprocess.CompletedProcess[str]:
    return _run(["index", "--index", str(INDEX), "--batch", str(batch)])


def _query(expr: str, out_id: str, *, env: dict[str, str] | None = None) -> dict:
    out = OUTPUT / f"{out_id}.json"
    proc = _run(
        [
            "query",
            "--index",
            str(INDEX),
            "--query",
            expr,
            "--output",
            str(out),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def _assert_hits_match(batch: Path, expr: str, actual: dict) -> None:
    expected = pipeline_reference(batch, expr)
    act_hits = [(h["docid"], round(h["score"], 8)) for h in actual["hits"]]
    exp_hits = [(h["docid"], round(h["score"], 8)) for h in expected["hits"]]
    assert act_hits == exp_hits, f"expected {exp_hits} got {act_hits}"


def test_cli_binary_exists() -> None:
    """Verify the xapian-weight-cli binary is installed on PATH."""
    assert CLI.is_file()


def test_rebuild_succeeds() -> None:
    """Verify agent code rebuilds without compile errors."""
    _build()


def test_protected_files_unmodified() -> None:
    """Anti-cheat: contract docs, fixtures, and decoy modules must stay unchanged."""
    for rel, digest in PROTECTED_SHA256.items():
        current = hashlib.sha256((APP / rel).read_bytes()).hexdigest()
        assert current == digest, rel


@pytest.mark.parametrize("batch,query", CATALOG)
def test_bundled_query_matches_reference(batch: str, query: str) -> None:
    """Bundled batches must rank documents per /app/docs/xapian-weight.md reference math."""
    _reset()
    batch_path = BATCHES / batch
    assert _index(batch_path).returncode == 0
    actual = _query(query, f"bundled-{batch}")
    _assert_hits_match(batch_path, query, actual)


def test_staging_snapshot_written_on_ingest() -> None:
    """Ingest must emit /app/state/index-staging.json with batch hash and collapsed terms."""
    _reset()
    batch_path = BATCHES / "tech-rust.jsonl"
    raw = batch_path.read_bytes()
    assert _index(batch_path).returncode == 0
    assert STAGING.is_file()
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert snap["doc_count"] == 2
    assert snap["batch_sha256"] == hashlib.sha256(raw).hexdigest()
    assert "memory" in snap["terms"] and "rust" in snap["terms"]


def test_staging_written_before_index_persist() -> None:
    """Staging snapshot must record written_before_index true before index update."""
    _reset()
    batch_path = BATCHES / "dup-collapse.jsonl"
    assert _index(batch_path).returncode == 0
    assert STAGING.is_file()
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert snap.get("written_before_index") is True


def test_positional_collapse_wdf_hidden() -> None:
    """Hidden collapse trap: adjacent duplicates must not inflate WDF via raw token counts."""
    _reset()
    batch = HIDDEN / "collapse-trap.jsonl"
    assert _index(batch).returncode == 0
    actual = _query("term OR spaced", "hidden-collapse")
    _assert_hits_match(batch, "term OR spaced", actual)


def test_synonym_max_not_sum_hidden() -> None:
    """Hidden synonym trap: oxidized must max with metal, not double-count WDF."""
    _reset()
    batch = HIDDEN / "synonym-trap.jsonl"
    assert _index(batch).returncode == 0
    actual = _query("metal OR smith", "hidden-synonym")
    _assert_hits_match(batch, "metal OR smith", actual)


def test_or_rare_term_idf_hidden() -> None:
    """Hidden OR trap: rare uniqueterm must still use full IDF weighting."""
    _reset()
    batch = BATCHES / "or-rare.jsonl"
    assert _index(batch).returncode == 0
    actual = _query("uniqueterm OR wolf", "hidden-or-rare")
    _assert_hits_match(batch, "uniqueterm OR wolf", actual)


def test_tb3_rare_cf_env_override() -> None:
    """TB3_RARE_CF env must not suppress IDF when threshold changes."""
    _reset()
    batch = BATCHES / "or-rare.jsonl"
    assert _index(batch).returncode == 0
    query = "uniqueterm OR wolf"
    actual_default = _query(query, "tb3-rare-default")
    _assert_hits_match(batch, query, actual_default)
    for rare_cf, label in [("0", "tb3-rare-zero"), ("99", "tb3-rare-high")]:
        actual = _query(query, label, env={"TB3_RARE_CF": rare_cf})
        _assert_hits_match(batch, query, actual)


def test_and_query_requires_all_terms() -> None:
    """AND queries must drop documents missing any query term."""
    _reset()
    batch = BATCHES / "tech-rust.jsonl"
    assert _index(batch).returncode == 0
    actual = _query("rust AND zebra", "and-miss")
    assert actual["hits"] == []


def test_index_cf_matches_reference_after_ingest() -> None:
    """Persisted collection frequencies must count each document once per term."""
    _reset()
    batch = BATCHES / "dup-collapse.jsonl"
    assert _index(batch).returncode == 0
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    from reference_xapian_weight import load_batch, rebuild_cf

    cf = rebuild_cf(load_batch(batch))
    assert idx["cf"] == cf


def test_tiebreak_docid_ascending_hidden() -> None:
    """Hidden tie-break trap: equal scores must rank lower docid first."""
    _reset()
    batch = HIDDEN / "tiebreak-trap.jsonl"
    query = "wolf OR alpha"
    assert _index(batch).returncode == 0
    actual = _query(query, "hidden-tiebreak")
    expected = pipeline_reference(batch, query)
    exp_hits = [(h["docid"], round(h["score"], 8)) for h in expected["hits"]]
    act_hits = [(h["docid"], round(h["score"], 8)) for h in actual["hits"]]
    assert len(exp_hits) >= 2
    assert exp_hits[0][1] == exp_hits[1][1]
    assert exp_hits[0][0] < exp_hits[1][0]
    assert act_hits == exp_hits


def test_patch_targets_exist() -> None:
    """Repair-scope Rust modules must be present for the agent."""
    for path in PATCH_TARGETS.values():
        assert path.is_file(), path
