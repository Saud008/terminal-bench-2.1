"""Reference oracle for sshap OpenSSH principals attestor."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fnmatch_case(pattern: str, value: str) -> bool:
    return fnmatch.fnmatch(value.lower(), pattern.lower())


def principal_specificity(principal: str) -> int:
    score = 1000
    if "@" in principal:
        score = 200
    if "*" in principal or "?" in principal:
        score = 400
    if "*" not in principal and "?" not in principal:
        score = 50
    return score


def principal_wildcard_bad(principal: str) -> bool:
    if "**" in principal:
        return True
    if "@" in principal:
        left, right = principal.split("@", 1)
        if "*" in left and left != "*":
            return True
        if "*" in right and not (right.startswith("*.") or right == "*"):
            return True
    elif "*" in principal and principal != "*":
        return True
    return False


def read_principal_files(principals_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for f in sorted(principals_dir.glob("*.principals")):
        scope = f.stem
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            deny = False
            text = line
            if line.startswith("!"):
                deny = True
                text = line[1:]
            rank = 0 if deny else principal_specificity(text)
            rows.append(
                {
                    "scope_id": scope,
                    "deny": deny,
                    "rank": rank,
                    "principal": text,
                }
            )
    rows.sort(key=lambda r: (r["scope_id"], int(r["deny"]), r["rank"], r["principal"]))
    return rows


def read_ca_material(ca_dir: Path) -> list[dict[str, Any]]:
    cas: list[dict[str, Any]] = []
    for f in sorted(ca_dir.glob("*.pub")):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            allowed = "*"
            if line.startswith("cert-authority"):
                m = re.search(r'principals="([^"]+)"', line)
                if m:
                    allowed = m.group(1)
                parts = line.split()
                key_type = next(p for p in parts if p.startswith("ssh-"))
                idx = parts.index(key_type)
                blob = parts[idx + 1]
                ca_id = parts[-1]
            else:
                parts = line.split()
                key_type, blob, ca_id = parts[0], parts[1], parts[2]
            principals_allowed = ["*"] if allowed == "*" else allowed.split(",")
            cas.append(
                {
                    "ca_id": ca_id,
                    "key_type": key_type,
                    "principals_allowed": principals_allowed,
                    "fingerprint": blob,
                }
            )
    return cas


def read_krl_revocations(krl: Path) -> list[str]:
    out: list[str] = []
    for line in krl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("fingerprint"):
            out.append(line.split()[1].lower())
    return sorted(out)


def ledger_fingerprint(principals: list[dict], cas: list[dict], revoked: list[str]) -> str:
    lines: list[str] = []
    for r in principals:
        lines.append(f"{r['scope_id']};{int(r['deny'])};{r['rank']};{r['principal']}")
    for c in sorted(cas, key=lambda x: x["ca_id"]):
        allowed = ",".join(c["principals_allowed"])
        lines.append(f"{c['ca_id']};{allowed}")
    for fp in sorted(revoked):
        lines.append(f"revoked;{fp}")
    return sha256_hex("\n".join(lines))


def build_trust_ledger(principals_dir: Path, ca_dir: Path, krl: Path) -> dict[str, Any]:
    principals = read_principal_files(principals_dir)
    cas = read_ca_material(ca_dir)
    revoked = read_krl_revocations(krl)
    digest = ledger_fingerprint(principals, cas, revoked)
    return {
        "schema_version": 1,
        "principals": principals,
        "cas": cas,
        "revoked": revoked,
        "ledger_fingerprint": digest,
    }


def resolve_match_scope(match_dir: Path, user: str, host: str) -> str:
    scope = "global"
    best_rank = 0
    for f in sorted(match_dir.glob("*.match")):
        mu = mh = cur = ""
        cur_rank = 0
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("Match"):
                mu_m = re.search(r"User ([^,]+)", line)
                mh_m = re.search(r"Host ([^,]+)", line)
                mu = mu_m.group(1) if mu_m else ""
                mh = mh_m.group(1) if mh_m else ""
                cur = ""
                cur_rank = (1 if mu else 0) + (1 if mh else 0)
            elif "AuthorizedPrincipalsFile" in line:
                path = line.split()[1]
                cur = Path(path).name.replace(".principals", "")
            if cur and mu and mh:
                if fnmatch_case(mu, user) and fnmatch_case(mh, host):
                    if cur_rank >= best_rank:
                        best_rank = cur_rank
                        scope = cur
    return scope


def row_matches(pattern: str, principal: str) -> bool:
    return fnmatch.fnmatch(principal.lower(), pattern.lower())


def decide_probe(ledger: dict, match_dir: Path, probe: dict) -> dict:
    pid = probe["probe_id"]
    user = probe["user"]
    host = probe["host"]
    principal = probe["principal"]
    fp = probe["key_fingerprint"].lower()
    signed = probe.get("signed_by_ca", False)
    ca_id = probe.get("ca_id") or ""
    scope = resolve_match_scope(match_dir, user, host)

    if fp in ledger.get("revoked", []):
        ad = sha256_hex(f"{pid}|deny|revoked||{scope}")
        return {
            "probe_id": pid,
            "verdict": "deny",
            "reason": "revoked",
            "winning_principal": "",
            "scope_id": scope,
            "binding_seal": ad,
        }

    if principal_wildcard_bad(principal):
        ad = sha256_hex(f"{pid}|deny|wildcard_denied||{scope}")
        return {
            "probe_id": pid,
            "verdict": "deny",
            "reason": "wildcard_denied",
            "winning_principal": "",
            "scope_id": scope,
            "binding_seal": ad,
        }

    if signed and ca_id:
        ca = next((c for c in ledger.get("cas", []) if c["ca_id"] == ca_id), None)
        allowed_list = ca["principals_allowed"] if ca else []
        if ca is None or not ("*" in allowed_list or principal in allowed_list):
            ad = sha256_hex(f"{pid}|deny|ca_scope||{scope}")
            return {
                "probe_id": pid,
                "verdict": "deny",
                "reason": "ca_scope",
                "winning_principal": "",
                "scope_id": scope,
                "binding_seal": ad,
            }

    best = ""
    best_deny = 1
    best_rank = 999999
    for row in ledger.get("principals", []):
        p_scope = row["scope_id"]
        if scope == "global":
            if p_scope != "global":
                continue
        else:
            if p_scope != scope:
                continue
        if not row_matches(row["principal"], principal):
            continue
        dnum = 0 if row["deny"] else 1
        rank = row["rank"]
        if dnum < best_deny or (dnum == best_deny and rank < best_rank):
            best_deny = dnum
            best_rank = rank
            best = row["principal"]
            if dnum == 0:
                ad = sha256_hex(f"{pid}|deny|principal_match|{best}|{scope}")
                return {
                    "probe_id": pid,
                    "verdict": "deny",
                    "reason": "principal_match",
                    "winning_principal": best,
                    "scope_id": scope,
                    "binding_seal": ad,
                }

    if best:
        ad = sha256_hex(f"{pid}|allow|principal_match|{best}|{scope}")
        return {
            "probe_id": pid,
            "verdict": "allow",
            "reason": "principal_match",
            "winning_principal": best,
            "scope_id": scope,
            "binding_seal": ad,
        }

    ad = sha256_hex(f"{pid}|deny|no_match||{scope}")
    return {
        "probe_id": pid,
        "verdict": "deny",
        "reason": "no_match",
        "winning_principal": "",
        "scope_id": scope,
        "binding_seal": ad,
    }


def emit_principals_attestation(ledger: dict, match_dir: Path, probes_doc: dict) -> dict:
    ids = sorted(p["probe_id"] for p in probes_doc["probes"])
    bindings = []
    digests = []
    probe_map = {p["probe_id"]: p for p in probes_doc["probes"]}
    for pid in ids:
        row = decide_probe(ledger, match_dir, probe_map[pid])
        bindings.append(row)
        digests.append(row["binding_seal"])
    bundle_seal = sha256_hex("".join(f"{d}\n" for d in digests))
    return {"schema_version": 1, "session_bindings": bindings, "bundle_seal": bundle_seal}


def reference_pipeline(
    principals_dir: Path,
    ca_dir: Path,
    krl: Path,
    match_dir: Path,
    probes_path: Path,
) -> tuple[dict, dict]:
    ledger = build_trust_ledger(principals_dir, ca_dir, krl)
    probes_doc = json.loads(probes_path.read_text(encoding="utf-8"))
    attestation = emit_principals_attestation(ledger, match_dir, probes_doc)
    return ledger, attestation
