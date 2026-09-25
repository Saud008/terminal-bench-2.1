"""Independent Python reference implementation of the cipgate attest math.

This module reimplements, from the docs contracts alone (trust-bind-policy,
revocation-seal, predicate-allowlist, builder-authz, quorum-attest,
witness-snapshot, attest-report-seal), the exact same algorithms the
corrected Go `cipgate attest` binary must implement: policy pack seed
selection/shuffle, policy merge, per-pull terminal-precedence evaluation,
witness fingerprints, and the audit_digest seal.

Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_digest(s: str) -> str:
    """Strip an optional 'sha256:' prefix and lowercase, per
    docs/trust-bind-policy.md."""
    s = s.strip().lower()
    if s.startswith("sha256:"):
        s = s[len("sha256:"):]
    return s


def match_glob(pattern: str, value: str) -> bool:
    """Full-string anchored glob match: '*' matches any run of characters,
    the match spans the entire value (not a substring). Mirrors
    internal/trustbind.MatchGlob in the corrected Go implementation."""
    if "*" not in pattern:
        return pattern == value

    parts = pattern.split("*")
    n = len(parts)

    if not value.startswith(parts[0]):
        return False
    rest = value[len(parts[0]):]

    last = parts[n - 1]
    if not rest.endswith(last):
        return False
    middle_span = rest[: len(rest) - len(last)] if last else rest

    pos = 0
    for part in parts[1: n - 1]:
        if part == "":
            continue
        idx = middle_span.find(part, pos)
        if idx < 0:
            return False
        pos = idx + len(part)
    return True


def parse_rfc3339(s: str) -> datetime:
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_rfc3339(dt: datetime) -> str:
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def image_digest(image: str) -> str:
    """Substring after the final '@' in image, normalized, per
    docs/trust-bind-policy.md."""
    idx = image.rfind("@")
    if idx < 0:
        return normalize_digest(image)
    return normalize_digest(image[idx + 1:])


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _list_json_files(dir_path: str) -> List[str]:
    names = [n for n in os.listdir(dir_path) if n.endswith(".json")]
    names.sort()
    return names


def load_trust_roots(dir_path: str) -> List[Dict[str, Any]]:
    roots = []
    for name in _list_json_files(dir_path):
        with open(os.path.join(dir_path, name), "r", encoding="utf-8") as f:
            roots.append(json.load(f))
    roots.sort(key=lambda r: r["root_id"])
    return roots


def load_envelopes(dir_path: str) -> List[Dict[str, Any]]:
    envs = []
    for name in _list_json_files(dir_path):
        with open(os.path.join(dir_path, name), "r", encoding="utf-8") as f:
            envs.append(json.load(f))
    envs.sort(key=lambda e: e["envelope_id"])
    return envs


def load_policy_pack(policies_root: str, name: str) -> Dict[str, Any]:
    pack_dir = os.path.join(policies_root, name)

    def _read(fname: str) -> Dict[str, Any]:
        with open(os.path.join(pack_dir, fname), "r", encoding="utf-8") as f:
            return json.load(f)

    builders = _read("builders.json")
    digest_deny = _read("digest-deny.json")
    predicates = _read("predicates.json")
    revocations = _read("revocations.json")

    return {
        "name": name,
        "builder_deny": builders.get("deny", []) or [],
        "builder_require": builders.get("require", []) or [],
        "digest_deny_pins": digest_deny.get("deny_digests", []) or [],
        "predicate_allow": predicates.get("allow", []) or [],
        "revocations": revocations.get("revocations", []) or [],
    }


def load_pulls(pulls_path: str) -> List[Dict[str, Any]]:
    pulls = []
    with open(pulls_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pulls.append(json.loads(line))
    return pulls


# ---------------------------------------------------------------------------
# Policy pack selection (seed) and merge
# ---------------------------------------------------------------------------

def select_packs(seed: str, packs: Sequence[str]) -> List[str]:
    """Per docs/quorum-attest.md "Policy pack selection (seed)"."""
    if not packs:
        return []

    digest = hashlib.sha256(seed.encode("utf-8")).digest()

    selected = []
    for i, name in enumerate(packs):
        idx = 5 + (i % 10)
        if digest[idx] % 2 == 1:
            selected.append(name)
    if not selected:
        selected = [packs[digest[7] % len(packs)]]

    out = list(selected)
    for i in range(len(out) - 1, 0, -1):
        j = digest[(i * 5 + 3) % len(digest)] % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out


def _union_strings(dst: List[str], src: Sequence[str]) -> List[str]:
    seen = set(dst)
    out = list(dst)
    for v in src:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def _merge_require(dst: List[str], src: Sequence[str]) -> List[str]:
    if not src:
        return dst
    return list(src)


def merge_policies(packs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Per docs/quorum-attest.md: digest-deny pins, predicate allows, and
    builder deny all union across packs; builder require replaces the prior
    list whenever a later pack's require list is non-empty; revocations
    union (concatenate)."""
    merged: Dict[str, Any] = {
        "digest_deny_pins": [],
        "predicate_allow": [],
        "builder_deny": [],
        "builder_require": [],
        "revocations": [],
    }
    for p in packs:
        merged["digest_deny_pins"] = _union_strings(merged["digest_deny_pins"], p["digest_deny_pins"])
        merged["predicate_allow"] = _union_strings(merged["predicate_allow"], p["predicate_allow"])
        merged["builder_deny"] = _union_strings(merged["builder_deny"], p["builder_deny"])
        merged["builder_require"] = _merge_require(merged["builder_require"], p["builder_require"])
        merged["revocations"] = merged["revocations"] + list(p["revocations"])
    return merged


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

def binds(root: Dict[str, Any], envelope: Dict[str, Any]) -> bool:
    """Per docs/trust-bind-policy.md: both issuer_glob and subject_glob must
    match."""
    return match_glob(root["issuer_glob"], envelope["issuer"]) and match_glob(
        root["subject_glob"], envelope["subject"]
    )


def digest_deny_hit(digest: str, pins: Sequence[str]) -> bool:
    """Per docs/quorum-attest.md: "exact digest match after
    normalization"."""
    return any(normalize_digest(p) == digest for p in pins)


def revocation_hit(digest: str, ts: datetime, revocations: Sequence[Dict[str, Any]]) -> bool:
    """Per docs/revocation-seal.md: half-open window [start, end), end
    exclusive."""
    for r in revocations:
        if normalize_digest(r["subject_digest"]) != digest:
            continue
        start = parse_rfc3339(r["start"]) if isinstance(r["start"], str) else r["start"]
        end = parse_rfc3339(r["end"]) if isinstance(r["end"], str) else r["end"]
        if start <= ts < end:
            return True
    return False


def predicate_allowed(pred_type: str, allow: Sequence[str]) -> bool:
    """Per docs/predicate-allowlist.md: exact equality."""
    return pred_type in allow


def builder_denied(builder_id: str, deny: Sequence[str]) -> bool:
    """Per docs/builder-authz.md: anchored glob match."""
    return any(match_glob(d, builder_id) for d in deny)


def builder_required(builder_id: str, require: Sequence[str]) -> bool:
    if not require:
        return True
    return any(match_glob(r, builder_id) for r in require)


# ---------------------------------------------------------------------------
# Per-pull evaluation (terminal precedence)
# ---------------------------------------------------------------------------

REASON_DIGEST_DENY = "digest_deny"
REASON_REVOCATION_HIT = "revocation_hit"
REASON_TRUST_UNBIND = "trust_unbind"
REASON_PREDICATE_REJECT = "predicate_reject"
REASON_BUILDER_DENY = "builder_deny"
REASON_BUILDER_REQUIRE_MISS = "builder_require_miss"
REASON_QUORUM_FAIL = "quorum_fail"
REASON_ADMIT_VERIFIED = "admit_verified"


def evaluate_pull(
    pull: Dict[str, Any],
    merged: Dict[str, Any],
    envelopes: Sequence[Dict[str, Any]],
    roots: Sequence[Dict[str, Any]],
    quorum_k: int,
) -> Dict[str, Any]:
    """Per docs/quorum-attest.md "Evaluation precedence (terminal)"."""
    digest = image_digest(pull["image"])
    ts = parse_rfc3339(pull["timestamp"]) if isinstance(pull["timestamp"], str) else pull["timestamp"]

    result = {
        "request_id": pull["request_id"],
        "image": pull["image"],
        "decision": "",
        "reason": "",
        "envelope_ids": [],
    }

    if digest_deny_hit(digest, merged["digest_deny_pins"]):
        result["decision"] = "deny"
        result["reason"] = REASON_DIGEST_DENY
        return result

    if revocation_hit(digest, ts, merged["revocations"]):
        result["decision"] = "deny"
        result["reason"] = REASON_REVOCATION_HIT
        return result

    matched = [e for e in envelopes if normalize_digest(e["subject_digest"]) == digest]
    trusted = [e for e in matched if any(binds(r, e) for r in roots)]

    if not trusted:
        result["decision"] = "deny"
        result["reason"] = REASON_TRUST_UNBIND
        return result

    pred_ok = [e for e in trusted if predicate_allowed(e["predicate_type"], merged["predicate_allow"])]
    if not pred_ok:
        result["decision"] = "deny"
        result["reason"] = REASON_PREDICATE_REJECT
        return result

    if any(builder_denied(e["builder_id"], merged["builder_deny"]) for e in pred_ok):
        result["decision"] = "deny"
        result["reason"] = REASON_BUILDER_DENY
        return result

    require_active = len(merged["builder_require"]) > 0
    if require_active:
        if not any(builder_required(e["builder_id"], merged["builder_require"]) for e in pred_ok):
            result["decision"] = "deny"
            result["reason"] = REASON_BUILDER_REQUIRE_MISS
            return result

    candidates = [
        e
        for e in pred_ok
        if not builder_denied(e["builder_id"], merged["builder_deny"])
        and (not require_active or builder_required(e["builder_id"], merged["builder_require"]))
    ]

    distinct_ids = sorted({e["envelope_id"] for e in candidates})
    if len(distinct_ids) < quorum_k:
        result["decision"] = "deny"
        result["reason"] = REASON_QUORUM_FAIL
        return result

    result["decision"] = "allow"
    result["reason"] = REASON_ADMIT_VERIFIED
    result["envelope_ids"] = distinct_ids
    return result


# ---------------------------------------------------------------------------
# Witness fingerprints
# ---------------------------------------------------------------------------

def _fingerprint_lines(vals: Sequence[str]) -> str:
    return sha256_hex("\n".join(sorted(vals)).encode("utf-8"))


def trust_fingerprint(roots: Sequence[Dict[str, Any]]) -> str:
    lines = [f"{r['root_id']}|{r['issuer_glob']}|{r['subject_glob']}" for r in roots]
    return _fingerprint_lines(lines)


def deny_fingerprint(pins: Sequence[str]) -> str:
    return _fingerprint_lines([normalize_digest(p) for p in pins])


def revoke_fingerprint(revocations: Sequence[Dict[str, Any]]) -> str:
    lines = []
    for r in revocations:
        start = parse_rfc3339(r["start"]) if isinstance(r["start"], str) else r["start"]
        end = parse_rfc3339(r["end"]) if isinstance(r["end"], str) else r["end"]
        subj = normalize_digest(r["subject_digest"])
        lines.append(f"{subj}|{format_rfc3339(start)}|{format_rfc3339(end)}")
    return _fingerprint_lines(lines)


def predicate_fingerprint(allow: Sequence[str]) -> str:
    return _fingerprint_lines(allow)


def builder_fingerprint(deny: Sequence[str], require: Sequence[str]) -> str:
    deny_lines = sorted("deny:" + d for d in deny)
    require_lines = sorted("require:" + r for r in require)
    parts = []
    if deny_lines:
        parts.append("\n".join(deny_lines))
    if require_lines:
        parts.append("\n".join(require_lines))
    return sha256_hex("\n".join(parts).encode("utf-8"))


def build_witness_snapshot(
    seed: str,
    quorum_k: int,
    selected_packs: Sequence[str],
    roots: Sequence[Dict[str, Any]],
    merged: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "seed": seed,
        "quorum_k": quorum_k,
        "policy_packs": list(selected_packs),
        "trust_fingerprint": trust_fingerprint(roots),
        "deny_fingerprint": deny_fingerprint(merged["digest_deny_pins"]),
        "revoke_fingerprint": revoke_fingerprint(merged["revocations"]),
        "predicate_fingerprint": predicate_fingerprint(merged["predicate_allow"]),
        "builder_fingerprint": builder_fingerprint(merged["builder_deny"], merged["builder_require"]),
    }


# ---------------------------------------------------------------------------
# Audit digest seal
# ---------------------------------------------------------------------------

def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def audit_digest(report: Dict[str, Any]) -> str:
    """Per docs/attest-report-seal.md "audit_digest": SHA-256 hex of the
    canonical JSON object (keys sorted, no insignificant whitespace)
    containing seed, quorum_k, policy_packs, trust_fingerprint,
    deny_fingerprint, revoke_fingerprint, predicate_fingerprint,
    builder_fingerprint, and a reduced results array."""
    reduced_results = []
    for r in report["results"]:
        ids = r.get("envelope_ids")
        if ids is None:
            ids = []
        reduced_results.append(
            {
                "decision": r["decision"],
                "envelope_ids": list(ids),
                "reason": r["reason"],
                "request_id": r["request_id"],
            }
        )

    payload = {
        "seed": report["seed"],
        "quorum_k": report["quorum_k"],
        "policy_packs": report["policy_packs"],
        "trust_fingerprint": report["trust_fingerprint"],
        "deny_fingerprint": report["deny_fingerprint"],
        "revoke_fingerprint": report["revoke_fingerprint"],
        "predicate_fingerprint": report["predicate_fingerprint"],
        "builder_fingerprint": report["builder_fingerprint"],
        "results": reduced_results,
    }
    return sha256_hex(canonical_json_bytes(payload))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_batch(
    config_path: str,
    pulls_path: str,
    roots_dir: Optional[str] = None,
    policies_root: Optional[str] = None,
    envelopes_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the full report dict matching `cipgate attest` output
    (including audit_digest), computed independently in Python from the
    docs contracts."""
    cfg = load_config(config_path)

    trust_roots_dir = roots_dir or cfg["trust_roots_dir"]
    policies_root_dir = policies_root or cfg["policies_root"]
    envelopes_directory = envelopes_dir or cfg["envelopes_dir"]

    seed = cfg["seed"]
    quorum_k = cfg["quorum_k"]

    roots = load_trust_roots(trust_roots_dir)
    envelopes = load_envelopes(envelopes_directory)

    selected = select_packs(seed, cfg.get("policy_packs", []))
    packs = [load_policy_pack(policies_root_dir, name) for name in selected]
    merged = merge_policies(packs)

    pulls = load_pulls(pulls_path)

    results = []
    for pull in pulls:
        res = evaluate_pull(pull, merged, envelopes, roots, quorum_k)
        results.append(res)

    snap = build_witness_snapshot(seed, quorum_k, selected, roots, merged)

    report = {
        "schema": "slsacip.attest.v1",
        "seed": seed,
        "quorum_k": quorum_k,
        "policy_packs": selected,
        "trust_fingerprint": snap["trust_fingerprint"],
        "deny_fingerprint": snap["deny_fingerprint"],
        "revoke_fingerprint": snap["revoke_fingerprint"],
        "predicate_fingerprint": snap["predicate_fingerprint"],
        "builder_fingerprint": snap["builder_fingerprint"],
        "results": results,
    }
    report["audit_digest"] = audit_digest(report)
    return report


if __name__ == "__main__":
    import sys

    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "/app/config/slsacip.json"
    pulls_p = sys.argv[2] if len(sys.argv) > 2 else "/app/fixtures/pull-waves/wave-north.jsonl"
    print(json.dumps(run_batch(cfg_path, pulls_p), indent=2, sort_keys=True))
