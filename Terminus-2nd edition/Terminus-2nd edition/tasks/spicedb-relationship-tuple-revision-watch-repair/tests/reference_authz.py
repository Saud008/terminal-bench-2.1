"""Independent reference for relation watch membership semantics."""

from __future__ import annotations

import base64
import json
import sqlite3
import struct
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ZED_PREFIX = "z1."

PROBE_CHECKS = (
    ("doc", "plan", "viewer", "user:alice"),
    ("doc", "plan", "viewer", "user:bob"),
)


def encode_zed_revision(revision: int) -> str:
    """Encode revision as 8-byte big-endian zed token (contract)."""
    payload = struct.pack(">Q", revision & 0xFFFFFFFFFFFFFFFF)
    return ZED_PREFIX + base64.b64encode(payload).decode("ascii").rstrip("=")


def decode_zed_revision(token: str) -> int:
    """Decode zed token to revision (8-byte contract)."""
    if not token.startswith(ZED_PREFIX):
        raise ValueError("invalid zed token prefix")
    raw = base64.b64decode(token[len(ZED_PREFIX) :] + "==")
    if len(raw) != 8:
        raise ValueError("invalid zed token length")
    return struct.unpack(">Q", raw)[0]


def watch_next_cursor(events: Iterable[dict], after_revision: int, namespace_filter: str) -> int:
    """Golden watch cursor: advance only on delivered (non-filtered) events."""
    pos = after_revision
    filt = (namespace_filter or "").strip()
    for ev in events:
        ns = ev.get("namespace", "")
        if filt and not ns.startswith(filt):
            continue
        rev = int(ev["revision"])
        pos = max(pos, rev)
    return pos


def expected_watch_filtered_skips(
    db_path: Path,
    after_revision: int,
    namespace_filter: str,
    limit: int = 100,
) -> int:
    """Count revision_log rows after cursor skipped by namespace_filter."""
    filt = (namespace_filter or "").strip()
    if not filt:
        return 0
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            """
            SELECT namespace FROM revision_log
            WHERE revision > ?
            ORDER BY revision ASC
            LIMIT ?
            """,
            (after_revision, limit),
        ).fetchall()
    finally:
        conn.close()
    return sum(1 for (ns,) in rows if not str(ns).startswith(filt))


def should_use_stale_snapshot(head: int, at_revision: int, threshold: int) -> bool:
    """Stale when lag <= threshold (per check-contract.md)."""
    lag = max(0, head - at_revision)
    return lag <= threshold


def caveat_passes(
    caveat_expr: str | None,
    subject: str,
    tombstone_at: int | None,
    at_revision: int,
) -> bool:
    """Tombstone applied before caveat evaluation."""
    if tombstone_at is not None and tombstone_at <= at_revision:
        return False
    if caveat_expr and caveat_expr.strip():
        data = json.loads(caveat_expr)
        allow = data.get("allow_subject", "")
        if allow and allow != subject:
            return False
    return True


@dataclass
class TupleRow:
    namespace: str
    object: str
    relation: str
    subject: str
    caveat_expr: str | None
    tombstone_revision: int | None


def load_active_tuples(db_path: Path, at_revision: int) -> list[TupleRow]:
    """Load tuples visible at revision from SQLite."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT namespace, object, relation, subject, caveat_expr, tombstone_revision
            FROM tuples
            WHERE created_revision <= ?
              AND (tombstone_revision IS NULL OR tombstone_revision > ?)
            """,
            (at_revision, at_revision),
        ).fetchall()
    finally:
        conn.close()
    out: list[TupleRow] = []
    for ns, obj, rel, subj, caveat, tomb in rows:
        out.append(
            TupleRow(
                namespace=ns,
                object=obj,
                relation=rel,
                subject=subj,
                caveat_expr=caveat,
                tombstone_revision=tomb,
            )
        )
    return out


def head_revision(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0])
    finally:
        conn.close()


def has_transitive_permission(
    db_path: Path,
    at_revision: int,
    namespace: str,
    obj: str,
    relation: str,
    subject: str,
) -> bool:
    """Independent closure expansion without server cache."""
    rows = load_active_tuples(db_path, at_revision)
    for t in rows:
        if (
            t.namespace == namespace
            and t.object == obj
            and t.relation == relation
            and t.subject == subject
        ):
            return True
    for t in rows:
        if t.namespace != namespace or t.object != obj or t.relation != relation:
            continue
        if "#" not in t.subject:
            continue
        group_ref, via_rel = t.subject.split("#", 1)
        for m in rows:
            if (
                m.namespace == namespace
                and m.object == group_ref
                and m.relation == via_rel
                and m.subject == subject
            ):
                return True
    return False


def live_check_allowed(
    db_path: Path,
    namespace: str,
    obj: str,
    relation: str,
    subject: str,
    at_revision: int,
) -> bool:
    """Live store evaluation at a revision (no snapshot fallback)."""
    if not has_transitive_permission(db_path, at_revision, namespace, obj, relation, subject):
        return False
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT caveat_expr, tombstone_revision
            FROM tuples
            WHERE namespace=? AND object=? AND relation=? AND subject=?
            """,
            (namespace, obj, relation, subject),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return True
    return caveat_passes(row[0], subject, row[1], at_revision)


def expected_check_summaries(db_path: Path, at_revision: int) -> list[dict]:
    """Probe summaries that revision-snapshot.json must embed."""
    out: list[dict] = []
    for ns, obj, rel, subj in PROBE_CHECKS:
        out.append(
            {
                "namespace": ns,
                "object": obj,
                "relation": rel,
                "subject": subj,
                "allowed": live_check_allowed(db_path, ns, obj, rel, subj, at_revision),
            }
        )
    return out


def expected_namespace_counts(db_path: Path, at_revision: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in load_active_tuples(db_path, at_revision):
        counts[t.namespace] = counts.get(t.namespace, 0) + 1
    return counts


def expected_export_report(db_path: Path, snapshot: dict) -> dict:
    """Authz report fields derived from snapshot + live head."""
    snap_rev = int(snapshot["revision"])
    summaries = expected_check_summaries(db_path, snap_rev)
    allowed = [s for s in summaries if s["allowed"]]
    denied = [s for s in summaries if not s["allowed"]]
    return {
        "generated_revision": head_revision(db_path),
        "snapshot_revision": snap_rev,
        "namespace_counts": expected_namespace_counts(db_path, snap_rev),
        "tuple_total": int(snapshot["tuple_count"]),
        "allowed_checks": allowed,
        "denied_checks": denied,
    }


def reference_check_allowed(
    db_path: Path,
    snapshot_path: Path,
    namespace: str,
    obj: str,
    relation: str,
    subject: str,
    zed_token: str,
    threshold: int,
) -> tuple[bool, bool]:
    """Return (allowed, used_stale) per contract."""
    at_revision = decode_zed_revision(zed_token)
    head = head_revision(db_path)

    if should_use_stale_snapshot(head, at_revision, threshold):
        snap = json.loads(snapshot_path.read_text(encoding="utf-8"))
        for summary in snap.get("check_summaries", []):
            if (
                summary["namespace"] == namespace
                and summary["object"] == obj
                and summary["relation"] == relation
                and summary["subject"] == subject
            ):
                return bool(summary["allowed"]), True
        return False, True

    return live_check_allowed(db_path, namespace, obj, relation, subject, at_revision), False


def bump_revision_counter(db_path: Path, value: int) -> None:
    """Set meta revision counter for high-revision zed token tests."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE meta SET value=? WHERE key='revision'", (value,))
        conn.commit()
    finally:
        conn.close()
