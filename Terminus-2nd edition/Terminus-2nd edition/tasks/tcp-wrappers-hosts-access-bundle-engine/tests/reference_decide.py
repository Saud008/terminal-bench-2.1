"""Independent reference engine for hostsctl bundle merge and decide."""

from __future__ import annotations

import hashlib
import ipaddress
import json
from pathlib import Path
from typing import Any


def load_manifest(bundle_root: Path) -> dict[str, Any]:
    return json.loads((bundle_root / "manifest.json").read_text(encoding="utf-8"))


def load_aliases(bundle_root: Path, manifest: dict[str, Any]) -> dict[str, list[str]]:
    alias_rel = manifest.get("daemon_aliases")
    if alias_rel:
        path = bundle_root / alias_rel
    else:
        path = bundle_root / "daemon-aliases.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_daemon(name: str, aliases: dict[str, list[str]]) -> str:
    lower = name.lower()
    for canon, spellings in aliases.items():
        options = {canon.lower(), *[s.lower() for s in spellings]}
        if lower in options:
            return canon
    return name


def parse_fragment(
    bundle_root: Path,
    side: str,
    rel: str,
    aliases: dict[str, list[str]],
) -> list[dict[str, Any]]:
    text = (bundle_root / rel).read_text(encoding="utf-8")
    rules: list[dict[str, Any]] = []
    buf = ""
    line_no = 0
    for raw_line in text.splitlines():
        line_no += 1
        chunk = raw_line.rstrip("\n")
        if chunk.endswith("\\"):
            buf += chunk[:-1].rstrip()
            continue
        if buf:
            buf += chunk.lstrip()
        else:
            buf += chunk
        line = buf.strip()
        buf = ""
        if not line or line.startswith("#") or ":" not in line:
            continue
        left, right = line.split(":", 1)
        daemons_raw = [d.strip() for d in left.split(",") if d.strip()]
        daemons: list[str] = []
        for token in daemons_raw:
            if token == "ALL":
                if "ALL" not in daemons:
                    daemons.append("ALL")
                continue
            canon = canonical_daemon(token, aliases)
            if canon not in daemons:
                daemons.append(canon)
        part = right.strip()
        if part.upper().startswith("ALL EXCEPT"):
            rest = part[len("ALL EXCEPT") :].strip()
            subs = rest.split() if rest else []
            clients = ["ALL EXCEPT " + " ".join(subs)]
        else:
            clients = [p.strip() for p in part.split(",") if p.strip()]
        rules.append(
            {
                "side": side,
                "origin": rel,
                "line": line_no,
                "daemons": daemons,
                "clients": clients,
            }
        )
    return rules


def load_rules(bundle_root: Path) -> list[dict[str, Any]]:
    manifest = load_manifest(bundle_root)
    aliases = load_aliases(bundle_root, manifest)
    rules: list[dict[str, Any]] = []
    for rel in manifest.get("allow_files", []):
        rules.extend(parse_fragment(bundle_root, "allow", rel, aliases))
    for rel in manifest.get("deny_files", []):
        rules.extend(parse_fragment(bundle_root, "deny", rel, aliases))
    return rules


def merge_rules(bundle_root: Path) -> dict[str, Any]:
    manifest = load_manifest(bundle_root)
    rules = load_rules(bundle_root)
    allow = [r for r in rules if r["side"] == "allow"]
    deny = [r for r in rules if r["side"] == "deny"]
    merged = allow + deny
    for idx, rule in enumerate(merged):
        rule["index"] = idx
    return {
        "bundle": manifest["name"],
        "rules": merged,
        "stats": {
            "allow_rules": len(allow),
            "deny_rules": len(deny),
            "total_rules": len(merged),
        },
    }


def match_client(ip: str, pattern: str) -> bool:
    pat = pattern.strip()
    if pat.upper().startswith("ALL EXCEPT"):
        rest = pat[len("ALL EXCEPT") :].strip()
        subs = rest.split() if rest else []
        for sub in subs:
            if match_client(ip, sub):
                return False
        return True
    if pat == "ALL":
        return True
    if "/" in pat:
        net = ipaddress.ip_network(pat, strict=False)
        addr = ipaddress.ip_address(ip)
        if addr.version != net.version:
            return False
        return addr in net
    return ip == pat


def client_matches(ip: str, clients: list[str]) -> bool:
    return any(match_client(ip, client) for client in clients)


def daemon_matches(rule_daemons: list[str], query: str, aliases: dict[str, list[str]]) -> bool:
    canon = canonical_daemon(query, aliases)
    for token in rule_daemons:
        if token == "ALL":
            return True
        if token.lower() == canon.lower():
            return True
    return False


def decide(bundle_root: Path, daemon: str, ip: str) -> dict[str, Any]:
    manifest = load_manifest(bundle_root)
    aliases = load_aliases(bundle_root, manifest)
    merged = merge_rules(bundle_root)["rules"]
    canon = canonical_daemon(daemon, aliases)
    for rule in merged:
        if rule["side"] != "allow":
            continue
        if daemon_matches(rule["daemons"], daemon, aliases) and client_matches(
            ip, rule["clients"]
        ):
            return {
                "bundle": manifest["name"],
                "daemon": canon,
                "ip": ip,
                "decision": "allow",
                "matched_rule_index": rule["index"],
                "matched_side": "allow",
                "reason": "first_match",
            }
    for rule in merged:
        if rule["side"] != "deny":
            continue
        if daemon_matches(rule["daemons"], daemon, aliases) and client_matches(
            ip, rule["clients"]
        ):
            return {
                "bundle": manifest["name"],
                "daemon": canon,
                "ip": ip,
                "decision": "deny",
                "matched_rule_index": rule["index"],
                "matched_side": "deny",
                "reason": "first_match",
            }
    return {
        "bundle": manifest["name"],
        "daemon": canon,
        "ip": ip,
        "decision": "deny",
        "matched_rule_index": -1,
        "matched_side": "",
        "reason": "default_deny",
    }


def bundle_fingerprint(bundle_root: Path) -> str:
    """SHA-256 over manifest-listed fragments (matches golden_common.sh)."""
    manifest = load_manifest(bundle_root)
    h = hashlib.sha256()
    for rel in manifest.get("allow_files", []) + manifest.get("deny_files", []):
        path = bundle_root / rel
        h.update(rel.encode("utf-8"))
        h.update(b"\n")
        h.update(path.read_bytes())
        h.update(b"\n")
    h.update((bundle_root / "manifest.json").read_bytes())
    return h.hexdigest()


def publish_seal(merged: dict[str, Any]) -> str:
    """Side-order-sensitive publish seal (matches golden publish.sh)."""
    rules = merged["rules"]
    stats = merged["stats"]
    first_deny = next((i for i, r in enumerate(rules) if r["side"] == "deny"), len(rules))
    body = json.dumps(
        {
            "allow_rules": stats["allow_rules"],
            "deny_rules": stats["deny_rules"],
            "total_rules": stats["total_rules"],
            "first_deny_index": first_deny,
            "sides": [r["side"] for r in rules],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def seeded_last_octet(base_prefix: str, seed: str, slot: str) -> str:
    digest = hashlib.sha256(f"{seed}:{slot}".encode()).hexdigest()
    last = int(digest[:2], 16) % 200 + 10
    return f"{base_prefix}.{last}"
