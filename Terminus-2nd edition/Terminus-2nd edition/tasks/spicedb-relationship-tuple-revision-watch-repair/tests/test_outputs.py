"""Behavioral verifier for relation watch revision desk."""

from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from reference_authz import (
    bump_revision_counter,
    decode_zed_revision,
    encode_zed_revision,
    expected_check_summaries,
    expected_export_report,
    expected_namespace_counts,
    expected_watch_filtered_skips,
    head_revision,
    live_check_allowed,
    reference_check_allowed,
    watch_next_cursor,
)

APP = Path("/app")
CONFIG = APP / "config" / "relationwatch.json"
SNAPSHOT = APP / "state" / "revision-snapshot.json"
REPORT = APP / "output" / "authz-report.json"
DB = APP / "data" / "relationwatch.db"
CLI = Path("/usr/local/bin/relationwatchd")
BASE = "http://127.0.0.1:8787"
THRESHOLD = 2


def _stop_daemon() -> None:
    subprocess.run(["pkill", "-9", "-x", "relationwatchd"], check=False)
    time.sleep(0.25)


def _start_daemon() -> None:
    _stop_daemon()
    subprocess.Popen(
        [str(CLI), "serve", "--config", str(CONFIG)],
        cwd=APP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            urllib.request.urlopen(f"{BASE}/health", timeout=0.5)
            return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("relationwatchd did not start")


def _request(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        if not raw:
            return exc.code, {}
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def _reset() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def _build() -> None:
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _seed() -> int:
    status, body = _request("POST", "/v1/admin/seed", {"fixture": "tuples/base"})
    assert status == 200, body
    return int(body["revision"])


def _write_tuple(**fields: str) -> dict:
    status, body = _request("POST", "/v1/tuple/write", fields)
    assert status == 200, body
    return body


def _check(ns: str, obj: str, rel: str, subj: str, zed: str) -> dict:
    status, body = _request(
        "POST",
        "/v1/check",
        {
            "namespace": ns,
            "object": obj,
            "relation": rel,
            "subject": subj,
            "zed_token": zed,
        },
    )
    assert status == 200, body
    return body


def _watch(after: int, ns_filter: str = "", limit: int = 50) -> dict:
    status, body = _request(
        "POST",
        "/v1/watch",
        {
            "after_revision": after,
            "namespace_filter": ns_filter,
            "limit": limit,
        },
    )
    assert status == 200, body
    return body


def _delete_prefix(prefix: str) -> dict:
    status, body = _request("POST", "/v1/admin/delete-namespace-prefix", {"prefix": prefix})
    assert status == 200, body
    return body


def _bump_head_writes(count: int, prefix: str) -> list[dict]:
    """Append audit tuples to advance head without rewriting doc plan group edges."""
    bodies: list[dict] = []
    for i in range(count):
        bodies.append(
            _write_tuple(
                operation="TOUCH",
                namespace="audit",
                object=f"{prefix}{i}",
                relation="reader",
                subject=f"user:{prefix}{i}",
            )
        )
    return bodies


def _export() -> dict:
    status, body = _request("POST", "/v1/export", {})
    assert status == 200, body
    assert REPORT.is_file()
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _summary_key(summary: dict) -> tuple:
    return (
        summary["namespace"],
        summary["object"],
        summary["relation"],
        summary["subject"],
        bool(summary["allowed"]),
    )


@pytest.fixture(scope="module", autouse=True)
def daemon_once():
    _build()
    _reset()
    _start_daemon()
    yield
    _stop_daemon()


@pytest.fixture(autouse=True)
def fresh_state():
    _stop_daemon()
    _reset()
    _start_daemon()
    yield


def test_revision_snapshot_schema_after_seed():
    """Snapshot must include revision, namespaces, tuples, and computed probe summaries."""
    rev = _seed()
    assert SNAPSHOT.is_file()
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["revision"] == rev
    assert snap["tuple_count"] >= 4
    assert sorted(snap["namespaces"]) == sorted(set(snap["namespaces"]))
    assert "doc" in snap["namespaces"]
    assert "audit" in snap["namespaces"]
    assert isinstance(snap["tuples"], list) and len(snap["tuples"]) == snap["tuple_count"]
    for row in snap["tuples"]:
        assert row["active"] is True
        for key in ("namespace", "object", "relation", "subject"):
            assert key in row

    expected = expected_check_summaries(DB, rev)
    actual = snap["check_summaries"]
    assert len(actual) == len(expected)
    assert sorted(_summary_key(s) for s in actual) == sorted(_summary_key(s) for s in expected)
    alice = next(s for s in actual if s["subject"] == "user:alice")
    bob = next(s for s in actual if s["subject"] == "user:bob")
    assert alice["allowed"] is True
    assert bob["allowed"] is True


def test_snapshot_summaries_recomputed_after_mutation():
    """Each successful write must refresh check_summaries from live probe evaluation."""
    seed_rev = _seed()
    _write_tuple(
        operation="DELETE",
        namespace="doc",
        object="group:eng",
        relation="member",
        subject="user:alice",
    )
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["revision"] > seed_rev
    expected = expected_check_summaries(DB, int(snap["revision"]))
    assert sorted(_summary_key(s) for s in snap["check_summaries"]) == sorted(
        _summary_key(s) for s in expected
    )
    alice = next(s for s in snap["check_summaries"] if s["subject"] == "user:alice")
    assert alice["allowed"] is False


def test_watch_cursor_skips_filtered_revisions():
    """Filtered-out namespaces must not advance the watch cursor."""
    seed_rev = _seed()
    _write_tuple(
        operation="TOUCH",
        namespace="doc",
        object="scratch",
        relation="viewer",
        subject="user:scratch",
    )
    empty = _watch(seed_rev, "audit")
    assert (empty.get("events") or []) == []
    assert empty["next_cursor"] == seed_rev, empty
    assert empty["next_cursor"] == watch_next_cursor([], seed_rev, "audit")
    assert empty["filtered_skips"] == expected_watch_filtered_skips(
        DB, seed_rev, "audit", limit=100
    )
    assert empty["filtered_skips"] >= 1

    _write_tuple(
        operation="TOUCH",
        namespace="audit",
        object="trail",
        relation="reader",
        subject="user:dave",
    )
    delivered = _watch(seed_rev, "audit")
    assert delivered["events"], delivered
    assert delivered["next_cursor"] > seed_rev
    assert delivered["next_cursor"] == watch_next_cursor(
        delivered["events"], seed_rev, "audit"
    )
    assert delivered["filtered_skips"] == expected_watch_filtered_skips(
        DB, seed_rev, "audit", limit=100
    )
    assert delivered["filtered_skips"] >= 1


def test_caveat_denies_after_delete_at_later_revision():
    """Deleted caveat tuples must not grant permission after tombstone revision."""
    seed_rev = _seed()
    _bump_head_writes(6, "pre")
    token_seed = encode_zed_revision(seed_rev)
    assert _check("doc", "plan", "viewer", "user:bob", token_seed)["allowed"] is True

    _write_tuple(
        operation="DELETE",
        namespace="doc",
        object="plan",
        relation="viewer",
        subject="user:bob",
    )
    _bump_head_writes(5, "post")
    head = head_revision(DB)
    token_head = encode_zed_revision(head - 3)
    resp = _check("doc", "plan", "viewer", "user:bob", token_head)
    assert resp["allowed"] is False, resp
    assert resp["used_stale_snapshot"] is False


def test_zed_token_preserves_high_revision_bits():
    """Zed tokens must round-trip revisions above 32-bit range."""
    _seed()
    bump_revision_counter(DB, 4294967296)
    body = _write_tuple(
        operation="TOUCH",
        namespace="audit",
        object="high",
        relation="reader",
        subject="user:high",
    )
    expected_rev = int(body["revision"])
    assert expected_rev > 4294967296
    decoded = decode_zed_revision(body["zed_token"])
    assert decoded == expected_rev


def test_namespace_prefix_delete_denies_live_checks():
    """Deleting a namespace prefix must remove tuples from future live checks."""
    _seed()
    _write_tuple(
        operation="TOUCH",
        namespace="tenant/a",
        object="doc",
        relation="viewer",
        subject="user:dave",
    )
    _bump_head_writes(4, "lag")
    head = head_revision(DB)
    token = encode_zed_revision(head - 3)
    assert _check("tenant/a", "doc", "viewer", "user:dave", token)["allowed"] is True
    _delete_prefix("tenant/a")
    head2 = head_revision(DB)
    token2 = encode_zed_revision(head2)
    assert _check("tenant/a", "doc", "viewer", "user:dave", token2)["allowed"] is False


def test_check_uses_stale_snapshot_when_lag_within_threshold():
    """Within threshold, check must use refreshed snapshot summaries, not live-at-token."""
    seed_rev = _seed()
    # Mutate head so live-at-seed still allows alice, but current snapshot denies.
    _write_tuple(
        operation="DELETE",
        namespace="doc",
        object="group:eng",
        relation="member",
        subject="user:alice",
    )
    _bump_head_writes(1, "stale")
    head = head_revision(DB)
    assert head - seed_rev == THRESHOLD

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    alice_snap = next(s for s in snap["check_summaries"] if s["subject"] == "user:alice")
    assert alice_snap["allowed"] is False
    assert live_check_allowed(DB, "doc", "plan", "viewer", "user:alice", seed_rev) is True

    token = encode_zed_revision(seed_rev)
    resp = _check("doc", "plan", "viewer", "user:alice", token)
    assert resp["used_stale_snapshot"] is True
    assert resp["allowed"] is False


def test_check_uses_live_store_when_lag_exceeds_threshold():
    """Beyond threshold, check must evaluate live tuples at the token revision."""
    seed_rev = _seed()
    _write_tuple(
        operation="DELETE",
        namespace="doc",
        object="group:eng",
        relation="member",
        subject="user:alice",
    )
    _bump_head_writes(3, "live")
    head = head_revision(DB)
    assert head - seed_rev > THRESHOLD

    token = encode_zed_revision(seed_rev)
    resp = _check("doc", "plan", "viewer", "user:alice", token)
    assert resp["used_stale_snapshot"] is False
    assert resp["allowed"] is True


def test_check_matches_independent_reference():
    """Live and stale checks must match independent reference_authz computation."""
    seed_rev = _seed()
    token = encode_zed_revision(seed_rev)
    resp = _check("doc", "plan", "viewer", "user:alice", token)
    expected, stale = reference_check_allowed(
        DB,
        SNAPSHOT,
        "doc",
        "plan",
        "viewer",
        "user:alice",
        token,
        THRESHOLD,
    )
    assert resp["allowed"] == expected
    assert resp["used_stale_snapshot"] == stale


def test_export_authz_report_matches_snapshot_contract():
    """Export must write all documented authz-report fields from the snapshot."""
    _seed()
    _write_tuple(
        operation="TOUCH",
        namespace="audit",
        object="export-marker",
        relation="reader",
        subject="user:export",
    )
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    report = _export()
    expected = expected_export_report(DB, snap)

    assert report["generated_revision"] == expected["generated_revision"]
    assert report["snapshot_revision"] == expected["snapshot_revision"]
    assert report["snapshot_revision"] == snap["revision"]
    assert report["tuple_total"] == expected["tuple_total"]
    assert report["tuple_total"] == snap["tuple_count"]
    assert report["namespace_counts"] == expected["namespace_counts"]
    assert report["namespace_counts"] == expected_namespace_counts(DB, snap["revision"])
    assert sorted(_summary_key(s) for s in report["allowed_checks"]) == sorted(
        _summary_key(s) for s in expected["allowed_checks"]
    )
    assert sorted(_summary_key(s) for s in report.get("denied_checks") or []) == sorted(
        _summary_key(s) for s in expected["denied_checks"]
    )


def test_export_reflects_denied_probe_after_delete():
    """Denied probe rows must appear when snapshot summaries flip to deny."""
    _seed()
    _write_tuple(
        operation="DELETE",
        namespace="doc",
        object="plan",
        relation="viewer",
        subject="user:bob",
    )
    report = _export()
    denied_subjects = {c["subject"] for c in report.get("denied_checks") or []}
    allowed_subjects = {c["subject"] for c in report.get("allowed_checks") or []}
    assert "user:bob" in denied_subjects
    assert "user:bob" not in allowed_subjects
    assert "user:alice" in allowed_subjects


def test_hidden_watch_cursor_reference():
    """Hidden fixture: doc-only writes must not advance audit-filtered cursor."""
    seed_rev = _seed()
    _write_tuple(
        operation="TOUCH",
        namespace="doc",
        object="hidden-only",
        relation="viewer",
        subject="user:hidden",
    )
    resp = _watch(seed_rev, "audit")
    assert (resp.get("events") or []) == []
    assert resp["next_cursor"] == seed_rev
    assert resp["filtered_skips"] == expected_watch_filtered_skips(
        DB, seed_rev, "audit", limit=100
    )
    assert resp["filtered_skips"] >= 1


def test_prefix_delete_refreshes_snapshot_summaries():
    """Namespace prefix deletes must rewrite snapshot summaries and tuple counts."""
    _seed()
    _write_tuple(
        operation="TOUCH",
        namespace="tenant/a",
        object="doc",
        relation="viewer",
        subject="user:dave",
    )
    before = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert "tenant/a" in before["namespaces"]
    _delete_prefix("tenant/a")
    after = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert "tenant/a" not in after["namespaces"]
    assert after["revision"] > before["revision"]
    assert after["tuple_count"] == len(after["tuples"])
    expected = expected_check_summaries(DB, int(after["revision"]))
    assert sorted(_summary_key(s) for s in after["check_summaries"]) == sorted(
        _summary_key(s) for s in expected
    )
