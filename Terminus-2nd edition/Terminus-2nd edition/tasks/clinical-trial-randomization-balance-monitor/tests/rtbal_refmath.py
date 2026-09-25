"""Independent reference for rtbalctl balance monitor pipeline."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def fixture_root() -> Path:
    return Path(os.environ.get("TB3_FIXTURE_DIR", "/app/fixtures"))


def bucket_key(factors: dict[str, Any]) -> str:
    return json.dumps(factors, sort_keys=True, separators=(",", ":"))


def protocol_digest(protocol: dict[str, Any]) -> str:
    arms = sorted(str(a) for a in protocol["arms"])
    strata_rows = []
    for row in protocol["strata"]:
        strata_rows.append(
            {"stratum_id": row["stratum_id"], "bucket_key": bucket_key(row["factors"])}
        )
    strata_rows.sort(key=lambda r: r["stratum_id"])
    body = {
        "trial_id": protocol["trial_id"],
        "protocol_version": protocol["protocol_version"],
        "arms": arms,
        "block_sizes": protocol["block_sizes"],
        "seed_salt": protocol["seed_salt"],
        "strata": strata_rows,
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda r: (int(r["ts"]), int(r["seq"])))
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for row in ordered:
        key = (row["subject_id"], row["event"])
        if key not in best or int(row["seq"]) >= int(best[key]["seq"]):
            best[key] = row
    return sorted(best.values(), key=lambda r: (int(r["ts"]), int(r["seq"])))


def block_seed(stratum_id: str, trial_id: str, seed_salt: str) -> int:
    preimage = f"{trial_id}|{stratum_id}|{seed_salt}"
    digest = hashlib.sha256(preimage.encode()).digest()
    return int.from_bytes(digest[:8], "big")


def permute_block(arms: list[str], block_size: int, seed: int) -> list[str]:
    slots: list[str] = []
    per = block_size // max(len(arms), 1)
    for arm in arms:
        slots.extend([arm] * per)
    while len(slots) < block_size:
        slots.append(arms[len(slots) % len(arms)])
    state = seed
    for i in range(len(slots) - 1, 0, -1):
        state = (state * 6364136223846793005 + 1) & ((1 << 64) - 1)
        j = state % (i + 1)
        slots[i], slots[j] = slots[j], slots[i]
    return slots


def run_balance_body(root: Path, trial_id: str, chronicle_rows: list[dict[str, Any]]) -> dict[str, Any]:
    protocol = json.loads((root / "trials" / f"{trial_id}.json").read_text(encoding="utf-8"))
    venues = json.loads((root / "ceilings" / f"{trial_id}.json").read_text(encoding="utf-8"))
    caps = {k: int(v) for k, v in venues["site_caps"].items()}
    arms = [str(a) for a in protocol["arms"]]
    block_sizes = [int(b) for b in protocol["block_sizes"]]
    seed_salt = str(protocol["seed_salt"])
    digest = protocol_digest(protocol)
    history: list[tuple[str, str, str, str]] = []
    stratum_of: dict[str, str] = {}
    block_idx: dict[str, int] = {}
    block_pos: dict[str, int] = {}
    current_block: dict[str, list[str]] = {}
    active_site: dict[str, int] = {}
    withdrawn: set[str] = set()
    for row in chronicle_rows:
        subject = row["subject_id"]
        site = row["site_id"]
        stratum = row["stratum_id"]
        event = row["event"]
        stratum_of[subject] = stratum
        if event == "withdraw":
            if active_site.get(site, 0) > 0:
                active_site[site] -= 1
            withdrawn.add(subject)
            history.append((subject, "withdraw", "", site))
            continue
        if event != "enroll":
            continue
        if active_site.get(site, 0) >= caps.get(site, 10**9):
            history.append((subject, "cap_rejected", "", site))
            continue
        b_i = block_idx.setdefault(stratum, 0)
        pos = block_pos.setdefault(stratum, 0)
        bsize = block_sizes[b_i % len(block_sizes)]
        if stratum not in current_block or pos >= len(current_block[stratum]):
            current_block[stratum] = permute_block(
                arms, bsize, block_seed(stratum, trial_id, seed_salt) ^ b_i
            )
            block_pos[stratum] = 0
            pos = 0
        arm = current_block[stratum][pos]
        block_pos[stratum] = pos + 1
        if block_pos[stratum] >= bsize:
            block_idx[stratum] = b_i + 1
            block_pos[stratum] = 0
            current_block.pop(stratum, None)
        active_site[site] = active_site.get(site, 0) + 1
        history.append((subject, "assign", arm, site))
    arm_map: dict[str, str] = {}
    for subject, event, arm, _site in history:
        if event == "assign":
            arm_map[subject] = arm
    per_stratum = []
    for s in protocol["strata"]:
        sid = s["stratum_id"]
        a = b = 0
        for subject, arm in arm_map.items():
            if subject in withdrawn:
                continue
            if stratum_of.get(subject) != sid:
                continue
            if arm == "A":
                a += 1
            elif arm == "B":
                b += 1
        per_stratum.append({"stratum_id": sid, "arm_a": a, "arm_b": b, "active_total": a + b})
    skew_rows = [(int(r["arm_a"]), int(r["arm_b"])) for r in per_stratum]
    max_skew = max((abs(a - b) for a, b in skew_rows), default=0)
    site_history = []
    active_subjects: set[str] = set()
    for subject, event, _arm, site in history:
        if event == "assign":
            active_subjects.add(subject)
            site_history.append((site, subject, True))
        elif event == "withdraw" and subject in active_subjects:
            active_subjects.discard(subject)
            site_history.append((site, subject, False))
    counts: dict[str, int] = {}
    for site, _subject, active in site_history:
        if active:
            counts[site] = counts.get(site, 0) + 1
    venues_at_cap = sorted(site for site, cap in caps.items() if counts.get(site, 0) >= cap)
    open_slots = []
    for s in protocol["strata"]:
        sid = s["stratum_id"]
        b_i = block_idx.get(sid, 0)
        pos = block_pos.get(sid, 0)
        bsize = block_sizes[b_i % len(block_sizes)]
        open_slots.append({"stratum_id": sid, "remaining_slots": max(bsize - pos, 0), "block_size": bsize})
    run_id = 1
    return {
        "trial_id": trial_id,
        "protocol_digest": digest,
        "run_id": run_id,
        "per_stratum": per_stratum,
        "max_skew": max_skew,
        "venues_at_cap": venues_at_cap,
        "open_slots": open_slots,
    }


def reference_pipeline(root: Path, trial_id: str) -> dict[str, Any]:
    protocol = json.loads((root / "trials" / f"{trial_id}.json").read_text(encoding="utf-8"))
    log_path = root / "logs" / f"{trial_id}.ndjson"
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    normalized = normalize_rows(rows)
    latch = {
        "trial_id": trial_id,
        "protocol_version": protocol["protocol_version"],
        "arms": protocol["arms"],
        "block_sizes": protocol["block_sizes"],
        "strata": protocol["strata"],
        "seed_salt": protocol["seed_salt"],
        "protocol_digest": protocol_digest(protocol),
        "log_relpath": f"logs/{trial_id}.ndjson",
    }
    chronicle = {
        "trial_id": trial_id,
        "protocol_digest": latch["protocol_digest"],
        "raw_count": len(rows),
        "normalized_count": len(normalized),
        "rows": normalized,
    }
    balance = run_balance_body(root, trial_id, normalized)
    closure_digest = hashlib.sha256(
        f"{trial_id}|{balance['protocol_digest']}|{balance['max_skew']}|{balance['run_id']}".encode()
    ).hexdigest()
    closure = {
        "trial_id": trial_id,
        "protocol_digest": balance["protocol_digest"],
        "run_id": balance["run_id"],
        "per_stratum": balance["per_stratum"],
        "max_skew": balance["max_skew"],
        "venues_at_cap": balance["venues_at_cap"],
        "open_slots": balance["open_slots"],
        "closure_digest": closure_digest,
    }
    return {"latch": latch, "chronicle": chronicle, "balance": balance, "closure": closure}
