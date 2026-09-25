"""Independent reference math for oidcgov verification decisions."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def grace_sec(fallback: int) -> int:
    raw = os.environ.get("TB3_GRACE_SEC")
    if raw:
        try:
            v = int(raw)
            if v >= 0:
                return v
        except ValueError:
            pass
    return fallback if fallback > 0 else 120


def load_scenario(scenario: str, fixture_root: Path) -> tuple[list[dict], list[dict], dict]:
    base = fixture_root / "scenarios" / scenario
    timeline = []
    for line in (base / "jwks_timeline.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            timeline.append(json.loads(line))
    timeline.sort(key=lambda e: e["epoch"])
    tokens = []
    for line in (base / "token_batch.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            tokens.append(json.loads(line))
    policy = json.loads((base / "policy.json").read_text(encoding="utf-8"))
    return timeline, tokens, policy


def build_cache_snapshot(timeline: list[dict], scenario: str) -> dict:
    snap = {
        "scenario": scenario,
        "active_keys": [],
        "retired_keys": [],
        "revoked_kids": [],
        "cache_max_age_sec": 0,
        "grace_window_sec": 0,
        "last_timeline_epoch": 0,
    }
    retired_epochs: dict[str, int] = {}
    for ev in timeline:
        snap["last_timeline_epoch"] = ev["epoch"]
        snap["cache_max_age_sec"] = ev.get("cache_max_age_sec", 0)
        snap["grace_window_sec"] = ev.get("grace_window_sec", 0)
        snap["active_keys"] = []
        snap["retired_keys"] = []
        snap["revoked_kids"] = []
        for k in ev.get("keys", []):
            status = k.get("status")
            kid = k.get("kid", "")
            if status == "active":
                snap["active_keys"].append(dict(k))
            elif status == "retired":
                snap["retired_keys"].append(dict(k))
                retired_epochs[kid.lower()] = ev["epoch"]
            elif status == "revoked":
                snap["revoked_kids"].append(kid)
    snap["_retired_epochs"] = retired_epochs
    return snap


def kid_match(token_kid: str, key_kid: str) -> bool:
    return token_kid.strip().lower() == key_kid.strip().lower()


def find_key(token_kid: str, keys: list[dict]) -> dict | None:
    for k in keys:
        if kid_match(token_kid, k.get("kid", "")):
            return k
    return None


def issuer_ok(token_iss: str, policy_iss: str) -> bool:
    return token_iss.strip().lower() == policy_iss.strip().lower()


def audience_ok(token_aud: list[str], policy_aud: list[str]) -> bool:
    if not policy_aud:
        return True
    policy_set = {a.strip() for a in policy_aud}
    for ta in token_aud:
        if ta.strip() not in policy_set:
            return False
    return True


def cache_fresh(sig_epoch: int, last_epoch: int, max_age_sec: int) -> bool:
    return (last_epoch - sig_epoch) <= max_age_sec


def in_grace(sig_epoch: int, retired_epoch: int, grace: int) -> bool:
    return retired_epoch <= sig_epoch <= retired_epoch + grace


def is_revoked(kid: str, revoked: list[str]) -> bool:
    kid_l = kid.strip().lower()
    return any(kid_l == r.strip().lower() for r in revoked)


def evaluate_token(tok: dict, policy: dict, snap: dict) -> dict:
    if not issuer_ok(tok["iss"], policy["issuer"]):
        return {"token_id": tok["token_id"], "verdict": "reject", "reason_code": "issuer_mismatch"}
    if not audience_ok(tok.get("aud", []), policy.get("audiences", [])):
        return {"token_id": tok["token_id"], "verdict": "reject", "reason_code": "audience_mismatch"}
    if is_revoked(tok["kid"], snap["revoked_kids"]):
        return {"token_id": tok["token_id"], "verdict": "reject", "reason_code": "key_revoked"}
    if find_key(tok["kid"], snap["active_keys"]):
        if not cache_fresh(tok["signature_epoch"], snap["last_timeline_epoch"], snap["cache_max_age_sec"]):
            return {"token_id": tok["token_id"], "verdict": "reject", "reason_code": "cache_stale"}
        return {"token_id": tok["token_id"], "verdict": "accept", "reason_code": "active_key"}
    if find_key(tok["kid"], snap["retired_keys"]):
        retired_epoch = snap["_retired_epochs"].get(tok["kid"].strip().lower(), snap["last_timeline_epoch"])
        g = grace_sec(snap["grace_window_sec"])
        if in_grace(tok["signature_epoch"], retired_epoch, g):
            return {"token_id": tok["token_id"], "verdict": "accept", "reason_code": "grace_key"}
        return {"token_id": tok["token_id"], "verdict": "reject", "reason_code": "key_retired"}
    return {"token_id": tok["token_id"], "verdict": "reject", "reason_code": "kid_unknown"}


def reference_decisions(scenario: str, fixture_root: Path) -> list[dict]:
    timeline, tokens, policy = load_scenario(scenario, fixture_root)
    snap = build_cache_snapshot(timeline, scenario)
    out = [evaluate_token(t, policy, snap) for t in tokens]
    out.sort(key=lambda d: d["token_id"])
    return out


def reference_transcript_digest(scenario: str, fixture_root: Path) -> str:
    timeline, tokens, policy = load_scenario(scenario, fixture_root)
    payload = {"policy": policy, "scenario": scenario, "timeline": timeline, "tokens": tokens}
    data = json.dumps(payload, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def reference_governance_report(scenario: str, fixture_root: Path) -> dict:
    decisions = reference_decisions(scenario, fixture_root)
    report = {"scenario": scenario, "decision_count": len(decisions), "decisions": decisions}
    payload = {
        "decision_count": report["decision_count"],
        "decisions": report["decisions"],
        "scenario": report["scenario"],
    }
    data = json.dumps(payload, separators=(",", ":")).encode()
    report["report_digest"] = hashlib.sha256(data).hexdigest()
    return report
