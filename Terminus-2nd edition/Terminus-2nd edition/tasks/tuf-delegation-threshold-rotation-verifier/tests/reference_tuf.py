"""Independent reference for tufctl rotation verifier."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any


def canonical(obj: Any) -> str:
    if isinstance(obj, dict):
        parts = [json.dumps(k, separators=(",", ":")) + ":" + canonical(obj[k]) for k in sorted(obj.keys())]
        return "{" + ",".join(parts) + "}"
    if isinstance(obj, list):
        return "[" + ",".join(canonical(x) for x in obj) + "]"
    return json.dumps(obj, separators=(",", ":"))


def verify_hmac(signed: dict, sig_row: dict, keys: dict[str, dict]) -> bool:
    key = keys.get(sig_row["keyid"])
    if not key:
        return False
    pub = bytes.fromhex(key["keyval"]["public"])
    payload = canonical(signed).encode()
    expected = hmac.new(pub, payload, hashlib.sha256).hexdigest()
    return expected == sig_row["sig"]


def key_valid(key: dict, epoch: int) -> bool:
    return epoch < int(key["keyval"]["expires_epoch"])


def verify_doc(
    doc: dict,
    role: dict,
    keys: dict[str, dict],
    epoch: int,
    root_role_keyids: list[str] | None = None,
) -> dict[str, Any]:
    root_role_keyids = root_role_keyids or []
    signed = doc["signed"]
    valid = 0
    expired: list[str] = []
    reuse: list[str] = []
    seen: set[str] = set()
    for sig in doc["signatures"]:
        kid = sig["keyid"]
        if kid in root_role_keyids:
            reuse.append(kid)
            continue
        if kid not in role["keyids"]:
            continue
        if kid in seen:
            continue
        seen.add(kid)
        key = keys.get(kid)
        if not key:
            continue
        if not key_valid(key, epoch):
            expired.append(kid)
            continue
        if verify_hmac(signed, sig, keys):
            valid += 1
    return {
        "threshold_met": valid >= int(role["threshold"]),
        "valid_signatures": valid,
        "expired_keyids": expired,
        "reuse_violations": reuse,
    }


def literal_score(pattern: str) -> int:
    return sum(1 for c in pattern if c not in {"*", "/"})


def pattern_matches(path: str, pattern: str) -> bool:
    if "**" in pattern:
        prefix = pattern.removesuffix("/**")
        return path.startswith(prefix) and (len(path) == len(prefix) or path[len(prefix) :].startswith("/"))
    if "*" in pattern:
        parts = pattern.split("/")
        path_parts = path.split("/")
        if len(parts) != len(path_parts):
            return False
        for p, t in zip(parts, path_parts):
            if p != "*" and p != t:
                return False
        return True
    return path == pattern


def pick_delegation(path: str, delegations: list[dict]) -> dict | None:
    best: tuple[dict, int, str] | None = None
    for deleg in delegations:
        for pattern in deleg["paths"]:
            if pattern_matches(path, pattern):
                score = literal_score(pattern)
                name = deleg["name"]
                if best is None or score > best[1] or (score == best[1] and name < best[2]):
                    best = (deleg, score, name)
    return best[0] if best else None


def target_allowed(path: str, delegations: list[dict]) -> tuple[bool, str | None, str]:
    deleg = pick_delegation(path, delegations)
    if not deleg:
        return False, None, "no_delegation"
    for pattern in deleg["paths"]:
        if pattern_matches(path, pattern):
            return True, deleg["name"], "ok"
    return False, deleg["name"], "pattern_mismatch"


def load_staging(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_doc(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def reference_verify(meta_dir: Path, staging: dict[str, Any], epoch: int) -> dict[str, Any]:
    root = load_doc(meta_dir / "root.json")
    targets = load_doc(meta_dir / "targets.json")
    snapshot = load_doc(meta_dir / "snapshot.json")
    keys = staging["keys"]
    root_role = staging["root_role"]
    targets_role = staging["targets_role"]
    root_keyids = root_role["keyids"]

    root_v = verify_doc(root, root_role, keys, epoch)
    targets_v = verify_doc(targets, targets_role, keys, epoch, root_keyids)
    snap_v = verify_doc(snapshot, targets_role, keys, epoch, root_keyids)
    snapshot_link_ok = staging["snapshot_targets_version"] == staging["targets_version"]
    rotation_ok = (
        root_v["threshold_met"]
        and targets_v["threshold_met"]
        and snap_v["threshold_met"]
        and snapshot_link_ok
    )
    return {
        "epoch": epoch,
        "rotation_ok": rotation_ok,
        "snapshot_link_ok": snapshot_link_ok,
        "metadata": [
            {"role": "root", **root_v},
            {"role": "targets", **targets_v},
            {"role": "snapshot", **snap_v},
        ],
    }


def reference_report(staging: dict[str, Any], verify: dict[str, Any]) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    for path in sorted(staging["targets"].keys()):
        if verify["rotation_ok"]:
            allowed, delegation, reason = target_allowed(path, staging["delegations"])
        else:
            allowed, delegation, reason = False, None, "rotation_failed"
        decisions.append(
            {
                "path": path,
                "allowed": allowed,
                "delegation": delegation,
                "reason": reason,
            }
        )
    digest = hashlib.sha256(canonical(decisions).encode()).hexdigest()
    return {
        "epoch": verify["epoch"],
        "rotation_ok": verify["rotation_ok"],
        "decisions": decisions,
        "audit_digest": digest,
    }


def reference_rejected_lines(report: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for row in report["decisions"]:
        if not row["allowed"]:
            lines.append(
                json.dumps(
                    {
                        "path": row["path"],
                        "reason": row["reason"],
                        "delegation": row["delegation"],
                    },
                    separators=(",", ":"),
                )
            )
    return lines


def tb3_epoch_bias() -> int:
    return int(os.environ.get("TB3_EPOCH_BIAS", "0"))
