"""Behavioral verifier for Typesense typo-token fuzzy ranking id repair."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from reference_typesense_search import load_batch, pipeline_reference, staging_snapshot

APP = Path("/app")
CLI = Path("/usr/local/bin/typesense-search-cli")
INDEX = APP / "work" / "index.json"
OUTPUT = APP / "output"
STAGING = APP / "state" / "index-staging.json"
BATCHES = APP / "fixtures" / "documents"
HIDDEN = Path("/opt/verifier-fixtures/documents")

CATALOG = [
    ("typo-laptop.jsonl", "laptp", None),
    ("brand-filter.jsonl", "widget", "north"),
    ("unicode-tokens.jsonl", "café", None),
]

PATCH_TARGETS = {
    "token_dedupe": APP / "crates/ts-tokenize/src/token_dedupe.rs",
    "prefix_score": APP / "crates/ts-fuzzy/src/prefix_score.rs",
    "tiebreak": APP / "crates/ts-ranker/src/tiebreak.rs",
    "counter": APP / "crates/ts-facet/src/counter.rs",
    "search_stage": APP / "crates/search-export/src/search_stage.rs",
    "store": APP / "crates/ingest-stage/src/store.rs",
}

PROTECTED_RELS = (
    "config/search.json",
    "docs/typo-search.md",
    "docs/filter-rank-order.md",
    "docs/token-dedupe.md",
    "docs/docid-tiebreak.md",
    "docs/facet-counts.md",
    "docs/staging-snapshot.md",
    "docs/repair-scope.md",
    "fixtures/catalog.json",
    "fixtures/documents/typo-laptop.jsonl",
    "fixtures/documents/brand-filter.jsonl",
    "fixtures/documents/unicode-tokens.jsonl",
    "crates/typesense-search-cli/src/main.rs",
    "crates/ts-types/src/document.rs",
    "crates/ts-types/src/index.rs",
    "crates/ts-types/src/search.rs",
    "crates/ts-fuzzy/src/typo_expand.rs",
    "crates/ts-fuzzy/src/edit_distance.rs",
    "crates/ts-fuzzy/src/typo_wrap.rs",
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
        check=False,
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
        check=False,
    )


def _index(batch: Path) -> subprocess.CompletedProcess[str]:
    return _run(["index", "--index", str(INDEX), "--batch", str(batch)])


def _search(
    query: str,
    out_id: str,
    *,
    brand: str | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    out = OUTPUT / f"{out_id}.json"
    args = [
        "search",
        "--index",
        str(INDEX),
        "--query",
        query,
        "--output",
        str(out),
    ]
    if brand is not None:
        args.extend(["--filter-brand", brand])
    proc = _run(args, env=env)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def _assert_search_matches(
    batch: Path,
    query: str,
    actual: dict,
    *,
    brand: str | None = None,
) -> None:
    expected = pipeline_reference(batch, query, brand)
    act_hits = [(h["docid"], round(h["score"], 8)) for h in actual["hits"]]
    exp_hits = [(h["docid"], round(h["score"], 8)) for h in expected["hits"]]
    assert act_hits == exp_hits, f"expected {exp_hits} got {act_hits}"
    assert actual["facets"] == expected["facets"]


@pytest.fixture(autouse=True)
def _clean_environment() -> None:
    _reset()
    OUTPUT.mkdir(parents=True, exist_ok=True)


def test_cli_binary_exists() -> None:
    """Instruction requires typesense-search-cli on PATH at /usr/local/bin/typesense-search-cli."""
    assert CLI.is_file()


def test_rebuild_succeeds() -> None:
    """Instruction requires bash /app/scripts/rebuild.sh after Rust repairs compile cleanly."""
    _build()


def test_protected_files_unmodified() -> None:
    """Anti-cheat: docs, fixtures, CLI entrypoints, and decoy modules must stay unchanged."""
    for rel, digest in PROTECTED_SHA256.items():
        current = hashlib.sha256((APP / rel).read_bytes()).hexdigest()
        assert current == digest, rel


@pytest.mark.parametrize("batch,query,brand", CATALOG)
def test_bundled_search_matches_reference(batch: str, query: str, brand: str | None) -> None:
    """Bundled ingest/search must match reference math from /app/docs typo and filter contracts."""
    batch_path = BATCHES / batch
    assert _index(batch_path).returncode == 0
    actual = _search(query, f"bundled-{batch}", brand=brand)
    _assert_search_matches(batch_path, query, actual, brand=brand)


def test_staging_snapshot_written_on_ingest() -> None:
    """Ingest must write /app/state/index-staging.json with batch hash and deduped terms."""
    batch_path = BATCHES / "typo-laptop.jsonl"
    raw = batch_path.read_bytes()
    assert _index(batch_path).returncode == 0
    assert STAGING.is_file()
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    expected = staging_snapshot(raw, load_batch(batch_path))
    assert snap["doc_count"] == expected["doc_count"]
    assert snap["batch_sha256"] == expected["batch_sha256"]
    assert set(snap["terms"]) == set(expected["terms"])


def test_staging_written_before_index_persist() -> None:
    """Staging snapshot must record written_before_index true before /app/work/index.json update."""
    batch_path = BATCHES / "brand-filter.jsonl"
    assert _index(batch_path).returncode == 0
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert snap.get("written_before_index") is True


def test_filter_rank_order_hidden() -> None:
    """Hidden trap: typo expansion must rank full corpus before brand filter removes hits."""
    batch = HIDDEN / "filter-rank-trap.jsonl"
    query = "laptp"
    brand = "keep"
    assert _index(batch).returncode == 0
    actual = _search(query, "hidden-filter-rank", brand=brand)
    _assert_search_matches(batch, query, actual, brand=brand)
    docids = [h["docid"] for h in actual["hits"]]
    assert "z9" not in docids
    assert docids == ["z1", "z2"]


def test_docid_tiebreak_hidden() -> None:
    """Hidden trap: equal scores within 1e-9 must tie-break by ascending docid per docid-tiebreak.md."""
    batch = HIDDEN / "tiebreak-trap.jsonl"
    query = "alpha beta"
    assert _index(batch).returncode == 0
    actual = _search(query, "hidden-tiebreak")
    expected = pipeline_reference(batch, query)
    act_hits = [(h["docid"], round(h["score"], 8)) for h in actual["hits"]]
    exp_hits = [(h["docid"], round(h["score"], 8)) for h in expected["hits"]]
    assert len(exp_hits) >= 2
    assert exp_hits[0][1] == exp_hits[1][1]
    assert exp_hits[0][0] < exp_hits[1][0]
    assert act_hits == exp_hits


def test_facet_counts_filtered_hits_hidden() -> None:
    """Hidden trap: brand facet counts must include only documents in the filtered hit list."""
    batch = HIDDEN / "facet-trap.jsonl"
    query = "widget"
    brand = "north"
    assert _index(batch).returncode == 0
    actual = _search(query, "hidden-facet", brand=brand)
    _assert_search_matches(batch, query, actual, brand=brand)
    assert actual["facets"]["brand"] == {"north": 2}


def test_unicode_nfc_dedupe_hidden() -> None:
    """Hidden trap: NFC dedupe must keep circled unicode and ASCII a as separate index terms."""
    batch = HIDDEN / "unicode-trap.jsonl"
    assert _index(batch).returncode == 0
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    terms = set(idx["token_index"].keys())
    assert "ⓐ" in terms or "\u24d0" in terms
    assert "a" in terms
    assert terms.intersection({"ⓐ"}) and "a" in terms


def test_tb3_typo_distance_env_override() -> None:
    """Typo edit distance must honor TB3_TYPO_DISTANCE from the environment."""
    batch = BATCHES / "typo-laptop.jsonl"
    query = "laptp"
    assert _index(batch).returncode == 0
    for distance, label in [("1", "typo-default"), ("2", "typo-two")]:
        actual = _search(query, label, env={"TB3_TYPO_DISTANCE": distance})
        _assert_search_matches(batch, query, actual)


def test_patch_targets_exist() -> None:
    """Repair-scope.md modules must exist for the agent to edit."""
    for path in PATCH_TARGETS.values():
        assert path.is_file(), path
