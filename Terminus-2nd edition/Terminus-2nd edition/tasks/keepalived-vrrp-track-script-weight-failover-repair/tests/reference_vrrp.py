"""Independent reference for kv-sim VRRP track-script replay."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_events(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        obj = json.loads(line)
        events.append(
            {
                "event_id": str(obj["event_id"]),
                "ts": int(obj["ts"]),
                "track": str(obj["track"]),
                "status": str(obj["status"]),
                "exit_code": int(obj.get("exit_code", 0)),
            }
        )
    return events


def track_index(cfg: dict[str, Any]) -> dict[str, int]:
    return {t["name"]: i for i, t in enumerate(cfg["tracks"])}


def init_staging(cfg: dict[str, Any]) -> dict[str, Any]:
    tracks_state: dict[str, Any] = {}
    for t in cfg["tracks"]:
        tracks_state[t["name"]] = {
            "consecutive_fail": 0,
            "consecutive_ok": 0,
            "weight_active": False,
            "weight_value": int(t["weight"]),
        }
    base = int(cfg["base_priority"])
    return {
        "virtual_router_id": int(cfg["virtual_router_id"]),
        "base_priority": base,
        "priority_floor": int(cfg["priority_floor"]),
        "master_threshold": int(cfg["master_threshold"]),
        "effective_priority": base,
        "role": "MASTER" if base >= int(cfg["master_threshold"]) else "BACKUP",
        "advert_seq": 0,
        "notify_pending": False,
        "notify_complete": True,
        "applied_event_ids": [],
        "tracks": tracks_state,
    }


def active_weight_sum(staging: dict[str, Any]) -> int:
    return sum(
        int(meta["weight_value"])
        for meta in staging["tracks"].values()
        if meta["weight_active"]
    )


def compute_effective(staging: dict[str, Any]) -> int:
    base = int(staging["base_priority"])
    floor = int(staging["priority_floor"])
    return max(floor, base + active_weight_sum(staging))


def role_for_effective(staging: dict[str, Any], effective: int) -> str:
    return "MASTER" if effective >= int(staging["master_threshold"]) else "BACKUP"


def apply_fall_race(staging: dict[str, Any], cfg: dict[str, Any]) -> bool:
    order = track_index(cfg)
    candidates: list[str] = []
    for name, meta in staging["tracks"].items():
        tcfg = next(t for t in cfg["tracks"] if t["name"] == name)
        if meta["consecutive_fail"] >= int(tcfg["fall"]) and not meta["weight_active"]:
            candidates.append(name)
    activated = False
    for name in sorted(candidates, key=lambda n: order.get(n, 999)):
        staging["tracks"][name]["weight_active"] = True
        activated = True
    return activated


def apply_track_event(staging: dict[str, Any], cfg: dict[str, Any], ev: dict[str, Any]) -> None:
    name = ev["track"]
    tcfg = next(t for t in cfg["tracks"] if t["name"] == name)
    meta = staging["tracks"][name]
    if ev["status"] == "fail":
        meta["consecutive_fail"] += 1
        meta["consecutive_ok"] = 0
    else:
        meta["consecutive_ok"] += 1
        meta["consecutive_fail"] = 0
        if meta["weight_active"] and meta["consecutive_ok"] >= int(tcfg["rise"]):
            meta["weight_active"] = False
            staging["effective_priority"] = compute_effective(staging)


def bump_advert(staging: dict[str, Any], prev_role: str) -> None:
    if prev_role == "MASTER" and staging["role"] == "BACKUP":
        staging["advert_seq"] = 0
    elif staging["role"] == "MASTER":
        staging["advert_seq"] = int(staging.get("advert_seq", 0)) + 1


def apply_event(staging: dict[str, Any], cfg: dict[str, Any], ev: dict[str, Any]) -> None:
    if ev["event_id"] in staging["applied_event_ids"]:
        return
    apply_track_event(staging, cfg, ev)
    race_activated = apply_fall_race(staging, cfg)
    if ev["status"] == "fail" or race_activated:
        staging["effective_priority"] = compute_effective(staging)
    prev_role = staging["role"]
    staging["role"] = role_for_effective(staging, staging["effective_priority"])
    if prev_role != staging["role"]:
        staging["notify_pending"] = True
        staging["notify_complete"] = False
    bump_advert(staging, prev_role)
    staging["applied_event_ids"].append(ev["event_id"])


def build_export(staging: dict[str, Any], last_event_id: str | None) -> dict[str, Any]:
    weights = []
    for name in sorted(staging["tracks"], key=lambda s: s.encode()):
        meta = staging["tracks"][name]
        if meta["weight_active"]:
            weights.append({"track": name, "weight": int(meta["weight_value"])})
    return {
        "version": 1,
        "virtual_router_id": staging["virtual_router_id"],
        "role": staging["role"],
        "effective_priority": staging["effective_priority"],
        "advert_seq": staging["advert_seq"],
        "active_weights": weights,
        "last_event_id": last_event_id,
    }


def replay_events(events_path: Path, cfg_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    cfg = load_config(cfg_path)
    events = parse_events(events_path.read_text(encoding="utf-8"))
    staging = init_staging(cfg)
    last_id: str | None = None
    for ev in events:
        apply_event(staging, cfg, ev)
        last_id = ev["event_id"]
        if staging.get("notify_pending"):
            staging["notify_pending"] = False
            staging["notify_complete"] = True
    export = build_export(staging, last_id)
    return staging, export


def build_manifest(input_path: Path, snapshot: dict[str, Any]) -> dict[str, str]:
    inp = hashlib.sha256(input_path.read_bytes()).hexdigest()
    snap = hashlib.sha256(
        json.dumps(snapshot, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return {"input_sha256": inp, "snapshot_sha256": snap}


def config_check(conf_path: Path, cfg_path: Path) -> dict[str, Any]:
    cfg = load_config(cfg_path)
    names: list[str] = []
    for line in conf_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("chk_"):
            names.append(line)
    track_by_name = {t["name"]: t for t in cfg["tracks"]}
    tracks_checked: list[str] = []
    scripts_run: list[dict[str, int | str]] = []
    all_ok = True
    for name in names:
        script = track_by_name[name]["script"]
        proc = subprocess.run([script], capture_output=True, text=True, check=False)
        tracks_checked.append(name)
        scripts_run.append({"track": name, "exit_code": proc.returncode})
        if proc.returncode != 0:
            all_ok = False
    return {
        "tracks_checked": tracks_checked,
        "scripts_run": scripts_run,
        "all_scripts_ok": all_ok,
    }


def build_seed_events(seed: str) -> str:
    lines = [
        json.dumps(
            {
                "event_id": f"seed-{seed}-1",
                "ts": 9000,
                "track": "chk_disk",
                "status": "fail",
                "exit_code": 1,
            }
        ),
        json.dumps(
            {
                "event_id": f"seed-{seed}-2",
                "ts": 9001,
                "track": "chk_disk",
                "status": "fail",
                "exit_code": 1,
            }
        ),
    ]
    return "\n".join(lines) + "\n"
