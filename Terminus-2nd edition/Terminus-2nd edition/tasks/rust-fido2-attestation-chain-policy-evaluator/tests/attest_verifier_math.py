"""Independent trust decision math for fido2eval."""
from __future__ import annotations

import hashlib
import json
import struct
import uuid
from pathlib import Path
from typing import Any


def parse_auth_data(hex_str: str) -> tuple[bool, int, str]:
    raw = bytes.fromhex(hex_str)
    flags = raw[32]
    sign_count = struct.unpack(">I", raw[33:37])[0]
    uv = (flags & 0x04) != 0
    aaguid_bytes = raw[37:53]
    aaguid = str(uuid.UUID(bytes=aaguid_bytes)).lower()
    return uv, sign_count, aaguid


def chain_valid(links: list[dict[str, str]]) -> bool:
    if not links:
        return False
    for link in links:
        if link["role"] == "root" and link["subject_fp"] != link["issuer_fp"]:
            return False
    for i in range(len(links) - 1):
        if links[i]["issuer_fp"] != links[i + 1]["subject_fp"]:
            return False
    return True


def lookup_aaguid(reg: dict[str, Any], aaguid: str) -> dict[str, Any] | None:
    key = str(uuid.UUID(aaguid)).lower()
    return reg["entries"].get(key)


def uv_ok(policy: dict[str, Any], uv: bool) -> bool:
    mode = policy["user_verification"]
    if mode in ("discouraged", "preferred"):
        return True
    if mode == "required":
        return uv
    return False


def trust_rank(level: str) -> int:
    return {"rejected": 0, "untrusted": 1, "trusted": 2}[level]


def reference_trust_report(
    batch_id: str,
    bundle_path: Path,
    policy_path: Path,
    metadata_path: Path,
) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    reg = json.loads(metadata_path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    decisions: list[dict[str, Any]] = []
    summary = {"trusted": 0, "untrusted": 0, "rejected": 0, "dedupe_blocked": 0}
    for tr in bundle["transcripts"]:
        cid = tr["credential_id"]
        is_dup = cid in seen
        seen.add(cid)
        uv, sign_count, _parsed = parse_auth_data(tr["auth_data_hex"])
        chain_ok = chain_valid(tr["cert_chain"])
        meta = lookup_aaguid(reg, tr["aaguid"])
        reasons: list[str] = []
        level = "trusted"
        if not chain_ok:
            reasons.append("chain_invalid")
            level = "rejected"
        if tr["attestation_format"] not in policy["allowed_formats"]:
            reasons.append("format_blocked")
            level = "rejected"
        if meta is None:
            reasons.append("unknown_aaguid")
            level = "untrusted"
        if not uv_ok(policy, uv):
            reasons.append("uv_policy")
            level = "rejected"
        if sign_count < policy["min_sign_count"]:
            reasons.append("sign_count_low")
            level = "rejected"
        if policy["reject_duplicate_credential_id"] and is_dup:
            reasons.append("duplicate_credential")
            level = "rejected"
            summary["dedupe_blocked"] += 1
        if meta is not None:
            root = tr["cert_chain"][-1]["subject_fp"]
            if root != meta["trust_anchor_fp"]:
                reasons.append("anchor_mismatch")
                if level == "trusted":
                    level = "untrusted"
        if level == "trusted":
            summary["trusted"] += 1
        elif level == "untrusted":
            summary["untrusted"] += 1
        else:
            summary["rejected"] += 1
        decisions.append(
            {
                "credential_id": cid,
                "aaguid": tr["aaguid"],
                "trust_level": level,
                "reasons": reasons,
                "sign_count": sign_count,
            }
        )
    decisions.sort(key=lambda d: (trust_rank(d["trust_level"]), d["credential_id"]))
    rep = {
        "batch_id": batch_id,
        "policy_name": policy["name"],
        "decisions": decisions,
        "summary": summary,
        "audit_digest": "",
    }
    body = json.dumps(
        {
            "batch_id": batch_id,
            "policy_name": policy["name"],
            "trusted": summary["trusted"],
            "untrusted": summary["untrusted"],
            "rejected": summary["rejected"],
            "dedupe_blocked": summary["dedupe_blocked"],
            "decision_ids": [d["credential_id"] for d in decisions],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    rep["audit_digest"] = hashlib.sha256(body.encode()).hexdigest()
    return rep
