#!/usr/bin/env python3
"""Golden fw-risk-map engine (oracle)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Inline copy of reference algorithms
import hashlib
import re
from typing import Any

CHAIN_MAP = {"INPUT": "input", "FORWARD": "forward", "OUTPUT": "output"}
HOOK_PRIORITY = {"INPUT": 0, "FORWARD": 0, "OUTPUT": 0}
UNSUPPORTED_MODULES = frozenset({"recent", "limit", "mark", "addrtype"})


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def pair_fingerprint(manifest_path: Path, ipt_path: Path, nft_path: Path) -> str:
    return sha256_bytes(manifest_path.read_bytes() + ipt_path.read_bytes() + nft_path.read_bytes())


def _parse_chain_counters(line: str) -> tuple[int, int]:
    m = re.search(r"\[(\d+):(\d+)\]\s*$", line)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def normalize_iptables_match(rest: str) -> str:
    segments: list[str] = []
    proto_m = re.search(r"-p\s+(\S+)", rest)
    if proto_m:
        segments.append(f"proto={proto_m.group(1).lower()}")
    ct_m = re.search(r"--ctstate\s+(\S+)", rest)
    if ct_m:
        states = sorted(s.strip().lower() for s in ct_m.group(1).split(","))
        segments.append(f"ct={','.join(states)}")
    dports_m = re.search(r"--dports\s+(\S+)", rest)
    if dports_m:
        ports = sorted(int(p) for p in dports_m.group(1).split(",") if p.isdigit())
        segments.append(f"dport={','.join(str(p) for p in ports)}")
    if not segments:
        segments.append("match=empty")
    return "|".join(segments)


def parse_iptables_save(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    policies: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = []
    unsupported: list[str] = []
    ordinals: dict[str, int] = {c: 0 for c in CHAIN_MAP}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(":"):
            m = re.match(r"^:([A-Z]+)\s+(\S+)", line)
            if not m or m.group(1) not in CHAIN_MAP:
                continue
            pkts, bytes_ = _parse_chain_counters(line)
            policies.append(
                {
                    "chain": m.group(1),
                    "ordinal": 0,
                    "policy": m.group(2).upper(),
                    "match_key": "",
                    "target": m.group(2).upper(),
                    "counter_packets": pkts,
                    "counter_bytes": bytes_,
                    "hook_priority": HOOK_PRIORITY[m.group(1)],
                }
            )
            continue
        if not line.startswith("-A "):
            continue
        body = line[3:].strip()
        chain_m = re.match(r"^(\S+)\s+(.*)$", body)
        if not chain_m or chain_m.group(1) not in CHAIN_MAP:
            continue
        chain, rest = chain_m.group(1), chain_m.group(2)
        skip = any(re.search(rf"-m\s+{mod}\b", rest) for mod in UNSUPPORTED_MODULES)
        if skip:
            for mod in UNSUPPORTED_MODULES:
                if re.search(rf"-m\s+{mod}\b", rest) and mod not in unsupported:
                    unsupported.append(mod)
            continue
        pkts, bytes_ = _parse_chain_counters(rest)
        rest = re.sub(r"\s*\[\d+:\d+\]\s*$", "", rest).strip()
        match_key = normalize_iptables_match(rest)
        target_m = re.search(r"-j\s+(\S+)", rest)
        target = target_m.group(1).upper() if target_m else "UNSPEC"
        ordinals[chain] += 1
        rules.append(
            {
                "chain": chain,
                "ordinal": ordinals[chain],
                "policy": None,
                "match_key": match_key,
                "target": target,
                "counter_packets": pkts,
                "counter_bytes": bytes_,
                "hook_priority": HOOK_PRIORITY[chain],
            }
        )
    unsupported.sort()
    tuples = sorted(policies + rules, key=lambda r: (r["chain"], r["ordinal"]))
    return tuples, unsupported


def normalize_nft_match(line: str) -> str:
    segments: list[str] = []
    if re.search(r"\btcp\b", line, re.I):
        segments.append("proto=tcp")
    ct_m = re.search(r"ct\s+state\s+([\w,]+)", line, re.I)
    if ct_m:
        states = sorted(s.strip().lower() for s in ct_m.group(1).split(","))
        segments.append(f"ct={','.join(states)}")
    dport_m = re.search(r"dport\s*\{\s*([^}]+)\}", line, re.I)
    if dport_m:
        ports = sorted(int(p.strip()) for p in dport_m.group(1).split(",") if p.strip().isdigit())
        segments.append(f"dport={','.join(str(p) for p in ports)}")
    if not segments:
        segments.append("match=empty")
    return "|".join(segments)


def parse_nft_excerpt(text: str) -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = []
    ordinals: dict[str, int] = {}
    current_chain: str | None = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if re.search(r"chain\s+(\w+)", line, re.I):
            m = re.search(r"chain\s+(\w+)", line, re.I)
            current_chain = m.group(1).lower() if m else None
            pol_m = re.search(r"policy\s+(\w+)", line, re.I)
            if current_chain and pol_m:
                rev = {v: k for k, v in CHAIN_MAP.items()}
                ipt_chain = rev.get(current_chain, current_chain.upper())
                hook_pri = HOOK_PRIORITY.get(ipt_chain, 0)
                pri_m = re.search(r"priority\s+(-?\d+)", line, re.I)
                if pri_m:
                    hook_pri = int(pri_m.group(1))
                policies.append(
                    {
                        "chain": ipt_chain,
                        "ordinal": 0,
                        "policy": pol_m.group(1).upper(),
                        "match_key": "",
                        "target": pol_m.group(1).upper(),
                        "counter_packets": 0,
                        "counter_bytes": 0,
                        "hook_priority": hook_pri,
                    }
                )
                ordinals[current_chain] = 0
            continue
        if current_chain is None:
            continue
        if line in {"}", "};"}:
            current_chain = None
            continue
        rev = {v: k for k, v in CHAIN_MAP.items()}
        ipt_chain = rev.get(current_chain, current_chain.upper())
        pkts, bytes_ = 0, 0
        ctr_m = re.search(r"counter\s+packets\s+(\d+)\s+bytes\s+(\d+)", line, re.I)
        if ctr_m:
            pkts, bytes_ = int(ctr_m.group(1)), int(ctr_m.group(2))
            line = re.sub(r"counter\s+packets\s+\d+\s+bytes\s+\d+", "", line, flags=re.I).strip()
        verdict_m = re.search(r"\b(accept|drop|reject)\s*;?\s*$", line, re.I)
        if not verdict_m:
            continue
        if line.startswith(("type ", "policy ", "hook ")):
            continue
        ordinals[current_chain] = ordinals.get(current_chain, 0) + 1
        rules.append(
            {
                "chain": ipt_chain,
                "ordinal": ordinals[current_chain],
                "policy": None,
                "match_key": normalize_nft_match(line),
                "target": verdict_m.group(1).upper(),
                "counter_packets": pkts,
                "counter_bytes": bytes_,
                "hook_priority": HOOK_PRIORITY.get(ipt_chain, 0),
            }
        )
    return sorted(policies + rules, key=lambda r: (r["chain"], r["ordinal"]))


def build_policy_precedence(ipt_policies: list[dict], nft_policies: list[dict], nft_text: str) -> list[dict]:
    declare_order = [m.group(1).lower() for m in re.finditer(r"chain\s+(\w+)\s*\{", nft_text, re.I)]
    nft_by = {CHAIN_MAP.get(p["chain"], p["chain"].lower()): p for p in nft_policies if p["ordinal"] == 0}
    rows: list[dict[str, Any]] = []
    for pol in sorted(ipt_policies, key=lambda p: (p["hook_priority"], p["chain"])):
        chain = pol["chain"]
        nft_chain = CHAIN_MAP[chain]
        nft_pol = nft_by.get(nft_chain, {})
        hook_pri = pol["hook_priority"]
        pri_m = re.search(rf"chain\s+{nft_chain}\s*\{{[^}}]*?priority\s+(-?\d+)", nft_text, re.I | re.S)
        if pri_m:
            hook_pri = int(pri_m.group(1))
        nft_policy = nft_pol.get("policy", pol["policy"])
        rows.append(
            {
                "chain": chain,
                "nft_chain": nft_chain,
                "iptables_policy": pol["policy"],
                "nft_policy": str(nft_policy).lower(),
                "hook_priority": hook_pri,
                "precedence_rank": declare_order.index(nft_chain) + 1 if nft_chain in declare_order else 99,
            }
        )
    rows.sort(key=lambda r: (r["hook_priority"], r["chain"]))
    for i, row in enumerate(rows, 1):
        row["precedence_rank"] = i
    return rows


def staging_digest(ipt_tuples: list[dict], nft_tuples: list[dict], policy_precedence: list[dict]) -> str:
    ipt_blob = "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in ipt_tuples).encode()
    nft_blob = "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in nft_tuples).encode()
    pol_blob = json.dumps(policy_precedence, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(ipt_blob + nft_blob + pol_blob)


def ingest_pair(manifest_path: Path, state_dir: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ipt_path = Path(manifest["iptables_path"])
    nft_path = Path(manifest["nft_path"])
    ipt_tuples, unsupported = parse_iptables_save(ipt_path.read_text(encoding="utf-8"))
    nft_tuples = parse_nft_excerpt(nft_path.read_text(encoding="utf-8"))
    nft_text = nft_path.read_text(encoding="utf-8")
    ipt_policies = [t for t in ipt_tuples if t["ordinal"] == 0]
    nft_policies = [t for t in nft_tuples if t["ordinal"] == 0]
    policy_precedence = build_policy_precedence(ipt_policies, nft_policies, nft_text)
    digest = staging_digest(ipt_tuples, nft_tuples, policy_precedence)
    meta = {
        "pair_id": manifest["pair_id"],
        "pair_fingerprint": pair_fingerprint(manifest_path, ipt_path, nft_path),
        "staging_digest": digest,
        "iptables_sha256": sha256_file(ipt_path),
        "nft_sha256": sha256_file(nft_path),
        "tuple_counts": {"iptables": len(ipt_tuples), "nft": len(nft_tuples)},
        "policy_precedence": policy_precedence,
        "unsupported_features": unsupported,
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "iptables-tuples.ndjson").write_text(
        "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in ipt_tuples) + ("\n" if ipt_tuples else ""),
        encoding="utf-8",
    )
    (state_dir / "nft-tuples.ndjson").write_text(
        "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in nft_tuples) + ("\n" if nft_tuples else ""),
        encoding="utf-8",
    )
    (state_dir / "staging-meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    meta["iptables_tuples"] = ipt_tuples
    meta["nft_tuples"] = nft_tuples
    return meta


def export_report(staging: dict[str, Any], run_seq: int) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    counter_drift: list[dict[str, Any]] = []
    ipt_rules = [t for t in staging["iptables_tuples"] if t["ordinal"] > 0]
    nft_rules = [t for t in staging["nft_tuples"] if t["ordinal"] > 0]
    for row in staging["policy_precedence"]:
        if row["iptables_policy"].upper() != row["nft_policy"].upper():
            findings.append(
                {
                    "category": "chain_policy_precedence",
                    "severity": "high",
                    "chain": row["chain"],
                    "iptables_ordinal": 0,
                    "nft_ordinal": 0,
                    "detail": f"policy mismatch iptables={row['iptables_policy'].upper()} nft={row['nft_policy'].upper()}",
                }
            )
    nft_by_chain: dict[str, list[dict]] = {}
    for r in nft_rules:
        nft_by_chain.setdefault(r["chain"], []).append(r)
    for chain in sorted(set(r["chain"] for r in ipt_rules)):
        ipt_list = sorted([r for r in ipt_rules if r["chain"] == chain], key=lambda x: x["ordinal"])
        nft_list = sorted(nft_by_chain.get(chain, []), key=lambda x: x["ordinal"])
        ipt_by_key = {r["match_key"]: r for r in ipt_list}
        nft_by_key = {r["match_key"]: r for r in nft_list}
        if set(ipt_by_key) == set(nft_by_key) and ipt_by_key:
            ipt_ord_map = {k: ipt_by_key[k]["ordinal"] for k in ipt_by_key}
            nft_ord_map = {k: nft_by_key[k]["ordinal"] for k in nft_by_key}
            if ipt_ord_map != nft_ord_map:
                findings.append(
                    {
                        "category": "rule_ordering",
                        "severity": "medium",
                        "chain": chain,
                        "iptables_ordinal": None,
                        "nft_ordinal": None,
                        "detail": "rule order diverges within chain",
                    }
                )
        for key in sorted(set(ipt_by_key) & set(nft_by_key)):
            ipt_r = ipt_by_key[key]
            nft_r = nft_by_key[key]
            if ipt_r["target"] == nft_r["target"]:
                if ipt_r["counter_packets"] != nft_r["counter_packets"] or ipt_r["counter_bytes"] != nft_r["counter_bytes"]:
                    counter_drift.append(
                        {
                            "chain": chain,
                            "ordinal": ipt_r["ordinal"],
                            "iptables_packets": ipt_r["counter_packets"],
                            "nft_packets": nft_r["counter_packets"],
                            "iptables_bytes": ipt_r["counter_bytes"],
                            "nft_bytes": nft_r["counter_bytes"],
                        }
                    )
                    findings.append(
                        {
                            "category": "counter_preservation",
                            "severity": "medium",
                            "chain": chain,
                            "iptables_ordinal": ipt_r["ordinal"],
                            "nft_ordinal": nft_r["ordinal"],
                            "detail": "counter mismatch on paired rule",
                        }
                    )
        for i, ipt_r in enumerate(ipt_list):
            nft_r = nft_list[i] if i < len(nft_list) else None
            if nft_r and ipt_r["match_key"] != nft_r["match_key"]:
                findings.append(
                    {
                        "category": "match_extension_normalization",
                        "severity": "low",
                        "chain": chain,
                        "iptables_ordinal": ipt_r["ordinal"],
                        "nft_ordinal": nft_r["ordinal"],
                        "detail": "match_key differs after normalization",
                    }
                )
    findings.sort(key=lambda f: (f["category"], f["chain"], f["iptables_ordinal"] or 0))
    summary = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        summary[f["severity"]] += 1
    return {
        "schema_version": "1",
        "pair_id": staging["pair_id"],
        "staging_digest": staging["staging_digest"],
        "run_seq": run_seq,
        "summary": summary,
        "findings": findings,
        "unsupported": list(staging["unsupported_features"]),
        "counter_drift": counter_drift,
        "policy_precedence": staging["policy_precedence"],
    }


def load_staging(state_dir: Path) -> dict[str, Any]:
    meta = json.loads((state_dir / "staging-meta.json").read_text(encoding="utf-8"))
    meta["iptables_tuples"] = [
        json.loads(raw)
        for raw in (state_dir / "iptables-tuples.ndjson").read_text().splitlines()
        if raw.strip()
    ]
    meta["nft_tuples"] = [
        json.loads(raw)
        for raw in (state_dir / "nft-tuples.ndjson").read_text().splitlines()
        if raw.strip()
    ]
    return meta


def cmd_ingest(manifest: Path, state_dir: Path) -> int:
    staging = ingest_pair(manifest, state_dir)
    run_seq_file = state_dir / "run-seq.json"
    fp = staging["pair_fingerprint"]
    if run_seq_file.is_file():
        ledger = json.loads(run_seq_file.read_text())
        run_seq = ledger.get("run_seq", 0)
        if ledger.get("last_pair_fingerprint") != fp:
            run_seq += 1
    else:
        run_seq = 1
    run_seq_file.write_text(
        json.dumps({"run_seq": run_seq, "last_pair_fingerprint": fp, "pair_id": staging["pair_id"]}),
        encoding="utf-8",
    )
    (state_dir / "active-pair.id").write_text(staging["pair_id"], encoding="utf-8")
    return 0


def cmd_export(pair_id: str, output: Path, state_dir: Path) -> int:
    if not (state_dir / "staging-meta.json").is_file():
        return 3
    active = (state_dir / "active-pair.id").read_text(encoding="utf-8").strip()
    if active != pair_id:
        return 3
    staging = load_staging(state_dir)
    run_seq = json.loads((state_dir / "run-seq.json").read_text())["run_seq"]
    report = export_report(staging, run_seq)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    ing = sub.add_parser("ingest")
    ing.add_argument("--pair", type=Path, required=True)
    ing.add_argument("--state-dir", type=Path, default=Path("/app/state"))
    exp = sub.add_parser("export")
    exp.add_argument("--pair-id", required=True)
    exp.add_argument("--output", type=Path, required=True)
    exp.add_argument("--state-dir", type=Path, default=Path("/app/state"))
    args = parser.parse_args()
    if args.cmd == "ingest":
        return cmd_ingest(args.pair, args.state_dir)
    return cmd_export(args.pair_id, args.output, args.state_dir)


if __name__ == "__main__":
    sys.exit(main())
