"""Independent reference for lootsettle settlement pipeline."""

from __future__ import annotations

import hashlib
import hmac
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def canonical_body(event: dict[str, Any]) -> str:
    body = {k: v for k, v in event.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def hmac_key(secret: str, pool_epoch: int) -> bytes:
    return f"{secret}:{pool_epoch}".encode()


def verify_signature(event: dict[str, Any], secret: str) -> bool:
    key = hmac_key(secret, int(event["pool_epoch"]))
    expected = hmac.new(key, canonical_body(event).encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, str(event.get("signature", "")))


def sort_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(events, key=lambda e: (int(e["timestamp_ms"]), int(e["seq"]), e["event_id"]))


def events_digest(events: list[dict[str, Any]]) -> str:
    ordered = sort_events(events)
    payload = "\n".join(canonical_body(e) for e in ordered)
    return hashlib.sha256(payload.encode()).hexdigest()


def load_season(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_season_by_id(seasons_dir: Path, season_id: str) -> dict[str, Any]:
    for path in sorted(seasons_dir.glob("*.json")):
        season = load_season(path)
        if season["season_id"] == season_id:
            return season
    raise KeyError(season_id)


def load_events(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def apply_season_carryover(player: dict[str, Any], new_season: dict[str, Any]) -> None:
    carried = int(player["pity_legendary"] * float(new_season["carry_ratio"]))
    player["pity_legendary"] = carried
    player["season_id"] = new_season["season_id"]


def apply_pity_after_pull(player: dict[str, Any], rarity: str) -> None:
    if rarity == "legendary":
        player["pity_legendary"] = 0
    else:
        player["pity_legendary"] = int(player["pity_legendary"]) + 1


def process_grant(
    player: dict[str, Any],
    season: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    item_id = event["item_id"]
    rarity = event["rarity"]
    if item_id in player["inventory"]:
        delta = int(season["duplicate_shards"][rarity])
        player["shards"] = int(player["shards"]) + delta
        return {
            "action": "duplicate_shard",
            "event_id": event["event_id"],
            "player_id": event["player_id"],
            "season_id": season["season_id"],
            "item_id": item_id,
            "rarity": rarity,
            "seq": int(event["seq"]),
            "timestamp_ms": int(event["timestamp_ms"]),
            "shard_delta": delta,
        }
    player["inventory"].append(item_id)
    player["inventory"].sort()
    return {
        "action": "grant",
        "event_id": event["event_id"],
        "player_id": event["player_id"],
        "season_id": season["season_id"],
        "item_id": item_id,
        "rarity": rarity,
        "seq": int(event["seq"]),
        "timestamp_ms": int(event["timestamp_ms"]),
    }


def duplicate_skip_audit(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": "duplicate_skip",
        "event_id": event["event_id"],
        "player_id": event["player_id"],
        "season_id": event["season_id"],
        "item_id": event["item_id"],
        "rarity": event["rarity"],
        "seq": int(event["seq"]),
        "timestamp_ms": int(event["timestamp_ms"]),
        "reason": "duplicate_event_id",
    }


def reference_settle(
    events: list[dict[str, Any]],
    seasons_dir: Path,
    *,
    processed: set[str] | None = None,
    generation_start: int = 0,
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    players: dict[str, Any] = {}
    audit_log: list[dict[str, Any]] = []
    seen = set(processed or ())
    generation = generation_start + 1
    for event in sort_events(events):
        if event["event_id"] in seen:
            audit_log.append(duplicate_skip_audit(event))
            continue
        season = load_season_by_id(seasons_dir, event["season_id"])
        if not verify_signature(event, season["hmac_secret"]):
            raise ValueError(f"bad signature {event['event_id']}")
        if int(event["pool_epoch"]) != int(season["pool_epoch"]):
            raise ValueError(f"pool epoch mismatch {event['event_id']}")
        player = players.setdefault(
            event["player_id"],
            {
                "season_id": event["season_id"],
                "inventory": [],
                "shards": 0,
                "pity_legendary": 0,
            },
        )
        if player["season_id"] != event["season_id"]:
            new_season = load_season_by_id(seasons_dir, event["season_id"])
            apply_season_carryover(player, new_season)
        audit_log.append(process_grant(player, season, event))
        apply_pity_after_pull(player, event["rarity"])
        player["season_id"] = event["season_id"]
        seen.add(event["event_id"])
    ledger = {"players": players}
    return ledger, audit_log, generation


def reference_staging(
    events: list[dict[str, Any]],
    season: dict[str, Any],
    staging_generation: int,
) -> dict[str, Any]:
    validated = deepcopy(events)
    return {
        "events": validated,
        "events_digest": events_digest(validated),
        "season_id": season["season_id"],
        "pool_epoch": int(season["pool_epoch"]),
        "staging_generation": staging_generation,
    }


def settlement_digest(report: dict[str, Any]) -> str:
    body = {k: v for k, v in report.items() if k != "settlement_digest"}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def reference_report(
    staging: dict[str, Any],
    ledger: dict[str, Any],
    generation: int,
    audit_log: list[dict[str, Any]],
) -> dict[str, Any]:
    sorted_audit = sorted(audit_log, key=lambda a: (a["timestamp_ms"], a["seq"], a["event_id"]))
    report = {
        "audit_log": sorted_audit,
        "events_digest": staging["events_digest"],
        "generation": generation,
        "layout_version": 1,
        "players": ledger["players"],
        "pool_epoch": staging["pool_epoch"],
        "season_id": staging["season_id"],
        "settlement_digest": "",
        "staging_generation": staging["staging_generation"],
    }
    report["settlement_digest"] = settlement_digest(report)
    return report


def reference_replay(
    season_path: Path,
    events_path: Path,
    seasons_dir: Path,
    *,
    staging_generation: int = 1,
    generation_start: int = 0,
) -> dict[str, Any]:
    season = load_season(season_path)
    events = load_events(events_path)
    for event in events:
        event_season = load_season_by_id(seasons_dir, event["season_id"])
        if not verify_signature(event, event_season["hmac_secret"]):
            raise ValueError(event["event_id"])
        if int(event["pool_epoch"]) != int(event_season["pool_epoch"]):
            raise ValueError(event["event_id"])
    staging = reference_staging(events, season, staging_generation)
    ledger, audit_log, generation = reference_settle(events, seasons_dir, generation_start=generation_start)
    return reference_report(staging, ledger, generation, audit_log)


def mutate_carry_ratio(season: dict[str, Any], seed: str) -> dict[str, Any]:
    out = deepcopy(season)
    bump = (sum(ord(c) for c in seed) % 7) + 1
    out["carry_ratio"] = round(min(0.9, float(out["carry_ratio"]) + bump * 0.01), 2)
    return out


def mutate_duplicate_shards(season: dict[str, Any], seed: str) -> dict[str, Any]:
    out = deepcopy(season)
    bump = (sum(ord(c) for c in seed) % 5) + 1
    for key in out["duplicate_shards"]:
        out["duplicate_shards"][key] = int(out["duplicate_shards"][key]) + bump
    return out
