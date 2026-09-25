"""Behavioral verifier for promingest remote-write ingest."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from reference_decode import (
    build_write_request,
    encode_block,
    expected_snapshot,
    expected_staging_record,
)

APP = Path("/app")
BASE = "http://127.0.0.1:9090"
RESET = APP / "scripts" / "reset-state.sh"
START = APP / "scripts" / "start-server.sh"
STAGING_DIR = APP / "data" / "ingest"
SEEDS = json.loads((APP / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]
TB3_ROOT = Path(os.environ.get("TB3_FIXTURE_DIR", "/opt/verifier-fixtures"))
HIDDEN_SEEDS = json.loads((TB3_ROOT / "hidden-seeds.json").read_text(encoding="utf-8"))["seeds"]

PROTECTED_SHA256 = {
    "fixtures/seeds.json": "",
    "fixtures/le-catalog.json": "",
}


def sha256_file(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


def _populate_hashes() -> None:
    for rel in list(PROTECTED_SHA256):
        PROTECTED_SHA256[rel] = sha256_file(rel)


_populate_hashes()


def post_write(body: bytes) -> int:
    req = urllib.request.Request(
        f"{BASE}/api/v1/write",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-protobuf"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def fetch_snapshot(seed: str) -> dict:
    with urllib.request.urlopen(f"{BASE}/api/v1/snapshot?seed={seed}", timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def reset_and_post(seed: str) -> None:
    subprocess.run(["bash", str(RESET)], check=True)
    subprocess.run(["bash", str(START)], check=True)
    body = encode_block(build_write_request(seed))
    status = post_write(body)
    assert status == 204, status


def snapshots_match(got: dict, want: dict) -> None:
    assert got["seed"] == want["seed"]
    assert got["sequence"] == want["sequence"]
    assert got["series"] == want["series"]


@pytest.mark.parametrize("seed", SEEDS)
def test_snapshot_matches_reference(seed: str) -> None:
    """Exported snapshot must match the independent decode reference."""
    reset_and_post(seed)
    got = fetch_snapshot(seed)
    snapshots_match(got, expected_snapshot(seed))


def test_bad_checksum_rejected() -> None:
    """Blocks with invalid body CRC must be rejected before decode."""
    seed = SEEDS[0]
    body = encode_block(build_write_request(seed), bad_crc=True)
    subprocess.run(["bash", str(RESET)], check=True)
    subprocess.run(["bash", str(START)], check=True)
    assert post_write(body) == 400


def test_native_histogram_schema_preserved() -> None:
    """Native histogram series must export schema version 2."""
    seed = SEEDS[1]
    reset_and_post(seed)
    snap = fetch_snapshot(seed)
    hist = next(s for s in snap["series"] if s["labels"].get("__name__") == "http_latency_bucket")
    assert hist["histogram_schema"] == 2


def test_exemplar_bound_to_matching_le() -> None:
    """Exemplar trace IDs must bind to buckets with the same le label."""
    seed = SEEDS[2]
    reset_and_post(seed)
    snap = fetch_snapshot(seed)
    want = expected_snapshot(seed)
    hist = next(s for s in snap["series"] if s["labels"].get("__name__") == "http_latency_bucket")
    want_hist = next(s for s in want["series"] if s["labels"].get("__name__") == "http_latency_bucket")
    assert hist["buckets"] == want_hist["buckets"]
    got_by_le = {bucket["le"]: bucket for bucket in hist["buckets"]}
    want_by_le = {bucket["le"]: bucket for bucket in want_hist["buckets"]}
    assert got_by_le["2.5"]["exemplar_trace_id"] == want_by_le["2.5"]["exemplar_trace_id"]
    assert got_by_le["0.1"]["exemplar_trace_id"] == want_by_le["0.1"]["exemplar_trace_id"]


def test_counter_reset_drops_exemplars() -> None:
    """Counter reset series must not retain bound exemplar trace IDs."""
    seed = SEEDS[3]
    reset_and_post(seed)
    snap = fetch_snapshot(seed)
    counter = next(s for s in snap["series"] if s["labels"].get("__name__") == "http_errors_total")
    for bucket in counter["buckets"]:
        assert "exemplar_trace_id" not in bucket or bucket.get("exemplar_trace_id", "") == ""


def test_name_label_not_overwritten() -> None:
    """Relabel dedup must keep the first __name__ label."""
    seed = SEEDS[0]
    reset_and_post(seed)
    snap = fetch_snapshot(seed)
    hist = next(s for s in snap["series"] if s["labels"].get("__name__") == "http_latency_bucket")
    assert hist["labels"]["__name__"] == "http_latency_bucket"


def test_snapshot_reference_requires_full_pipeline() -> None:
    """Full snapshot reference match requires staging plus export stages together."""
    seed = SEEDS[1]
    reset_and_post(seed)
    snap = fetch_snapshot(seed)
    snapshots_match(snap, expected_snapshot(seed))


def test_health_only_insufficient() -> None:
    """Health check success does not validate remote-write ingest behavior."""
    subprocess.run(["bash", str(RESET)], check=True)
    subprocess.run(["bash", str(START)], check=True)
    with urllib.request.urlopen(f"{BASE}/healthz", timeout=5) as resp:
        assert resp.status == 200
    snap = fetch_snapshot(SEEDS[0])
    assert snap["series"] == []


def test_protected_fixtures_unchanged() -> None:
    """Protected fixtures must not be edited by agents."""
    for rel, expected in PROTECTED_SHA256.items():
        assert sha256_file(rel) == expected, rel


def test_staging_file_written_on_accept() -> None:
    """Accepted writes must persist a staging JSON record on disk."""
    seed = SEEDS[0]
    reset_and_post(seed)
    staging_path = STAGING_DIR / f"{seed}.json"
    assert staging_path.is_file()
    got = json.loads(staging_path.read_text(encoding="utf-8"))
    want = expected_staging_record(seed)
    assert got["seed"] == want["seed"]
    assert got["sequence"] == want["sequence"]
    assert got["series"][0]["histogram_schema"] == 2


def test_staging_sequence_increments_on_rewrite() -> None:
    """Second accepted write for the same seed must bump staging sequence."""
    seed = SEEDS[2]
    subprocess.run(["bash", str(RESET)], check=True)
    subprocess.run(["bash", str(START)], check=True)
    body = encode_block(build_write_request(seed))
    assert post_write(body) == 204
    assert post_write(body) == 204
    snap = fetch_snapshot(seed)
    assert snap["sequence"] == 2
    staging = json.loads((STAGING_DIR / f"{seed}.json").read_text(encoding="utf-8"))
    assert staging["sequence"] == 2


def test_bad_checksum_leaves_no_staging_file() -> None:
    """Rejected checksum blocks must not create staging artifacts."""
    seed = SEEDS[1]
    body = encode_block(build_write_request(seed), bad_crc=True)
    subprocess.run(["bash", str(RESET)], check=True)
    subprocess.run(["bash", str(START)], check=True)
    assert post_write(body) == 400
    assert not (STAGING_DIR / f"{seed}.json").exists()


def test_snapshot_empty_without_staging() -> None:
    """Snapshot export must fail closed when staging record is missing."""
    subprocess.run(["bash", str(RESET)], check=True)
    subprocess.run(["bash", str(START)], check=True)
    snap = fetch_snapshot("missing-seed")
    assert snap["series"] == []
    assert snap["sequence"] == 0


def test_export_applies_relabel_not_ingest() -> None:
    """Relabel dedup must run during export, not during write handling."""
    seed = SEEDS[3]
    reset_and_post(seed)
    staging = json.loads((STAGING_DIR / f"{seed}.json").read_text(encoding="utf-8"))
    raw = staging["series"][0]["labels"]
    assert sum(1 for lp in raw if lp["name"] == "__name__") == 2
    snap = fetch_snapshot(seed)
    hist = next(s for s in snap["series"] if s["labels"].get("__name__") == "http_latency_bucket")
    assert hist["labels"]["__name__"] == "http_latency_bucket"


@pytest.mark.parametrize("seed", HIDDEN_SEEDS)
def test_hidden_snapshot_matches_reference(seed: str) -> None:
    """Hidden fixture seeds must match reference with reversed exemplar order."""
    reset_and_post(seed)
    got = fetch_snapshot(seed)
    snapshots_match(got, expected_snapshot(seed))


@pytest.mark.parametrize("seed", HIDDEN_SEEDS)
def test_hidden_exemplar_binding_by_le(seed: str) -> None:
    """Hidden seeds fail round-robin exemplar binding and require le matching."""
    reset_and_post(seed)
    snap = fetch_snapshot(seed)
    want = expected_snapshot(seed)
    hist = next(s for s in snap["series"] if s["labels"].get("__name__") == "http_latency_bucket")
    want_hist = next(s for s in want["series"] if s["labels"].get("__name__") == "http_latency_bucket")
    assert hist["buckets"] == want_hist["buckets"]


def test_hidden_staging_schema_not_downgraded() -> None:
    """Hidden histogram seeds require schema 2 preserved in staging files."""
    seed = HIDDEN_SEEDS[0]
    reset_and_post(seed)
    staging = json.loads((STAGING_DIR / f"{seed}.json").read_text(encoding="utf-8"))
    hist = next(s for s in staging["series"] if s["labels"][0]["value"] == "http_latency_bucket")
    assert hist["histogram_schema"] == 2


def test_double_write_snapshot_sequence() -> None:
    """Snapshot sequence must reflect the latest accepted write count."""
    seed = SEEDS[0]
    subprocess.run(["bash", str(RESET)], check=True)
    subprocess.run(["bash", str(START)], check=True)
    body = encode_block(build_write_request(seed))
    assert post_write(body) == 204
    assert post_write(body) == 204
    snap = fetch_snapshot(seed)
    assert snap["sequence"] == 2
    snapshots_match(snap, expected_snapshot(seed, sequence=2))
