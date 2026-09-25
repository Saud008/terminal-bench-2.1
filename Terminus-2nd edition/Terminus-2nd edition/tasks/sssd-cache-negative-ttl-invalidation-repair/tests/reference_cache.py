"""Independent reference for sssdcache negative TTL replay and export."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


KIND_PRIORITY = {
    "lookup_miss": 1,
    "cache_put": 2,
    "group_add_member": 3,
    "invalidate": 4,
    "cache_del": 5,
    "lookup_hit": 6,
}


@dataclass
class Stats:
    lines_read: int = 0
    ops_applied: int = 0
    parse_errors: int = 0
    lookup_miss: int = 0
    lookup_hit: int = 0
    cache_put: int = 0
    cache_del: int = 0
    negative_created: int = 0
    negative_refreshed: int = 0
    group_add_member: int = 0
    group_invalidations: int = 0
    explicit_invalidation: int = 0
    wal_checkpoints: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "lines_read": self.lines_read,
            "ops_applied": self.ops_applied,
            "parse_errors": self.parse_errors,
            "lookup_miss": self.lookup_miss,
            "lookup_hit": self.lookup_hit,
            "cache_put": self.cache_put,
            "cache_del": self.cache_del,
            "negative_created": self.negative_created,
            "negative_refreshed": self.negative_refreshed,
            "group_add_member": self.group_add_member,
            "group_invalidations": self.group_invalidations,
            "explicit_invalidation": self.explicit_invalidation,
            "wal_checkpoints": self.wal_checkpoints,
        }


@dataclass
class CacheState:
    domain_suffix: str
    negatives: dict[str, dict[str, Any]] = field(default_factory=dict)
    positives: dict[str, str] = field(default_factory=dict)
    principal_meta: dict[str, dict[str, str]] = field(default_factory=dict)
    groups: dict[str, dict[str, bool]] = field(default_factory=dict)
    last_ts: int = 0


def cache_key(domain: str, name: str) -> str:
    return domain.lower() + "\x00" + name


def load_config(path: Path) -> dict[str, Any]:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("negative_ttl_sec", 0) <= 0:
        cfg["negative_ttl_sec"] = 15
    if not cfg.get("domain_suffix"):
        cfg["domain_suffix"] = "example"
    override = os.environ.get("SSSD_DOMAIN_SUFFIX", "")
    if override:
        cfg["domain_suffix"] = override
    return cfg


def discover_jsonl(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    files = sorted(path.glob("*.jsonl"))
    return files


def parse_line(line: str) -> dict[str, Any]:
    raw = json.loads(line)
    return {
        "ts": int(raw.get("ts", 0)),
        "seq": int(raw.get("seq", 0)),
        "kind": str(raw.get("kind", "")),
        "domain": str(raw.get("domain", "")),
        "name": str(raw.get("name", "")),
        "group": str(raw.get("group", "")),
        "member": str(raw.get("member", "")),
        "value": str(raw.get("value", "")),
    }


def read_ops(ops_path: Path) -> tuple[list[dict[str, Any]], Stats]:
    stats = Stats()
    ops: list[dict[str, Any]] = []
    for file in discover_jsonl(ops_path):
        for line in file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            stats.lines_read += 1
            try:
                ops.append(parse_line(line))
            except json.JSONDecodeError:
                stats.parse_errors += 1
    return ops, stats


def sort_ops(ops: list[dict[str, Any]]) -> None:
    ops.sort(
        key=lambda o: (
            o["ts"],
            o["seq"],
            KIND_PRIORITY.get(o["kind"], 99),
        )
    )


def effective_domain(op: dict[str, Any], cfg: dict[str, Any]) -> str:
    if op["domain"]:
        return op["domain"]
    return str(cfg["domain_suffix"])


def on_lookup_miss(
    state: CacheState, domain: str, name: str, ts: int, ttl_sec: int, stats: Stats
) -> None:
    key = cache_key(domain, name)
    stats.lookup_miss += 1
    ttl_ms = ttl_sec * 1000
    neg = state.negatives.get(key)
    if neg is not None and ts < neg["expires_at"]:
        neg["miss_ts"] = ts
        neg["expires_at"] = ts + ttl_ms
        stats.negative_refreshed += 1
        return
    state.negatives[key] = {
        "domain": domain,
        "name": name,
        "miss_ts": ts,
        "expires_at": ts + ttl_ms,
    }
    stats.negative_created += 1


def remove_principal(state: CacheState, domain: str, name: str) -> None:
    key = cache_key(domain, name)
    state.positives.pop(key, None)
    state.negatives.pop(key, None)
    state.principal_meta.pop(key, None)


def on_lookup_hit(state: CacheState, domain: str, name: str, stats: Stats) -> None:
    stats.lookup_hit += 1
    remove_principal(state, domain, name)


def on_cache_put(
    state: CacheState, domain: str, name: str, value: str, stats: Stats
) -> None:
    key = cache_key(domain, name)
    state.negatives.pop(key, None)
    state.positives[key] = value
    state.principal_meta[key] = {"domain": domain, "name": name}
    stats.cache_put += 1


def on_cache_del(state: CacheState, domain: str, name: str, stats: Stats) -> None:
    remove_principal(state, domain, name)
    stats.cache_del += 1


def invalidate_principal(state: CacheState, domain: str, name: str, stats: Stats) -> None:
    key = cache_key(domain, name)
    if key in state.positives:
        state.positives.pop(key, None)
        state.principal_meta.pop(key, None)
    state.negatives.pop(key, None)
    stats.explicit_invalidation += 1


def collect_users(state: CacheState, group: str, out: dict[str, bool]) -> None:
    members = state.groups.get(group, {})
    for member in members:
        if member in state.groups:
            collect_users(state, member, out)
            continue
        out[member] = True


def invalidate_group_members(
    state: CacheState, group: str, nested: bool, stats: Stats
) -> None:
    members = state.groups.get(group)
    if not members:
        return
    users: dict[str, bool] = {}
    if nested:
        collect_users(state, group, users)
    else:
        for member in members:
            users[member] = True
    for user in users:
        remove_principal(state, state.domain_suffix, user)
        stats.group_invalidations += 1


def add_member(
    state: CacheState, group: str, member: str, nested: bool, stats: Stats
) -> None:
    if group not in state.groups:
        state.groups[group] = {}
    if state.groups[group].get(member):
        return
    state.groups[group][member] = True
    stats.group_add_member += 1
    invalidate_group_members(state, group, nested, stats)


def replay_ops(ops: list[dict[str, Any]], cfg: dict[str, Any]) -> tuple[CacheState, Stats]:
    state = CacheState(domain_suffix=str(cfg["domain_suffix"]))
    stats = Stats()
    sort_ops(ops)
    for op in ops:
        if not op["kind"]:
            stats.parse_errors += 1
            continue
        domain = effective_domain(op, cfg)
        if op["ts"] > state.last_ts:
            state.last_ts = op["ts"]
        kind = op["kind"]
        if kind == "lookup_miss":
            on_lookup_miss(state, domain, op["name"], op["ts"], int(cfg["negative_ttl_sec"]), stats)
        elif kind == "lookup_hit":
            on_lookup_hit(state, domain, op["name"], stats)
        elif kind == "cache_put":
            on_cache_put(state, domain, op["name"], op["value"], stats)
        elif kind == "cache_del":
            on_cache_del(state, domain, op["name"], stats)
        elif kind == "group_add_member":
            add_member(state, op["group"], op["member"], bool(cfg.get("nested_invalidation")), stats)
        elif kind == "invalidate":
            invalidate_principal(state, domain, op["name"], stats)
        else:
            stats.parse_errors += 1
            continue
        stats.ops_applied += 1
    return state, stats


def build_snapshot(state: CacheState, stats: Stats) -> dict[str, Any]:
    neg_keys = sorted(state.negatives)
    pos_keys = sorted(state.positives)
    group_names = sorted(state.groups)
    return {
        "snapshot_version": 1,
        "domain_suffix": state.domain_suffix,
        "evaluated_at_ms": state.last_ts,
        "negatives": [
            {
                "domain": state.negatives[k]["domain"],
                "name": state.negatives[k]["name"],
                "miss_ts": state.negatives[k]["miss_ts"],
                "expires_at": state.negatives[k]["expires_at"],
            }
            for k in neg_keys
        ],
        "positives": [
            {
                "domain": state.principal_meta[k]["domain"],
                "name": state.principal_meta[k]["name"],
                "value": state.positives[k],
            }
            for k in pos_keys
        ],
        "groups": [
            {
                "group": g,
                "members": sorted(state.groups[g]),
            }
            for g in group_names
        ],
        "stats": stats.as_dict(),
    }


def filter_active_negatives(
    negatives: list[dict[str, Any]], evaluated_at_ms: int
) -> list[dict[str, Any]]:
    return [n for n in negatives if n["expires_at"] > evaluated_at_ms]


def build_export(snap: dict[str, Any]) -> dict[str, Any]:
    active = filter_active_negatives(snap["negatives"], snap["evaluated_at_ms"])
    return {
        "domain_suffix": snap["domain_suffix"],
        "active_negatives": active,
        "positives": snap["positives"],
        "stats": snap["stats"],
    }


def reference_replay(ops_path: Path, config_path: Path) -> dict[str, Any]:
    cfg = load_config(config_path)
    ops, ingest_stats = read_ops(ops_path)
    state, replay_stats = replay_ops(ops, cfg)
    replay_stats.lines_read = ingest_stats.lines_read
    replay_stats.parse_errors += ingest_stats.parse_errors
    replay_stats.wal_checkpoints = 1
    snap = build_snapshot(state, replay_stats)
    snap["stats"]["wal_checkpoints"] = 1
    return build_export(snap)


def reference_snapshot(ops_path: Path, config_path: Path) -> dict[str, Any]:
    cfg = load_config(config_path)
    ops, ingest_stats = read_ops(ops_path)
    state, replay_stats = replay_ops(ops, cfg)
    replay_stats.lines_read = ingest_stats.lines_read
    replay_stats.parse_errors += ingest_stats.parse_errors
    replay_stats.wal_checkpoints = 1
    snap = build_snapshot(state, replay_stats)
    snap["stats"]["wal_checkpoints"] = 1
    return snap
