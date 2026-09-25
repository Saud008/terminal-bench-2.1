"""Independent reference for hitreplay collision sampling and export."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


def tick_to_frame(tick: int, tick_rate: int, fps: int) -> int:
    return (tick * fps + tick_rate // 2) // tick_rate


def tick_to_ms(tick: int, tick_rate: int) -> int:
    return tick * 1000 // tick_rate


def quat_normalize(q: list[float]) -> list[float]:
    x, y, z, w = q
    mag = math.sqrt(x * x + y * y + z * z + w * w)
    if mag == 0.0:
        return [0.0, 0.0, 0.0, 1.0]
    return [x / mag, y / mag, z / mag, w / mag]


def quat_slerp(q0: list[float], q1: list[float], t: float) -> list[float]:
    a = quat_normalize(q0)
    b = quat_normalize(q1)
    dot = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
    if dot < 0.0:
        b = [-b[0], -b[1], -b[2], -b[3]]
        dot = -dot
    if dot > 0.9995:
        out = [a[i] + t * (b[i] - a[i]) for i in range(4)]
        return quat_normalize(out)
    theta0 = math.acos(max(-1.0, min(1.0, dot)))
    sin_theta0 = math.sin(theta0)
    theta = theta0 * t
    s0 = math.sin(theta0 - theta) / sin_theta0
    s1 = math.sin(theta) / sin_theta0
    return quat_normalize([s0 * a[i] + s1 * b[i] for i in range(4)])


def lerp3(a: list[float], b: list[float], t: float) -> list[float]:
    return [a[i] + (b[i] - a[i]) * t for i in range(3)]


def rotate_vec_by_quat(v: list[float], q: list[float]) -> list[float]:
    x, y, z = v
    qx, qy, qz, qw = quat_normalize(q)
    ix = qw * x + qy * z - qz * y
    iy = qw * y + qz * x - qx * z
    iz = qw * z + qx * y - qy * x
    iw = -qx * x - qy * y - qz * z
    return [
        ix * qw + iw * -qx + iy * -qz - iz * -qy,
        iy * qw + iw * -qy + iz * -qx - ix * -qz,
        iz * qw + iw * -qz + ix * -qy - iy * -qx,
    ]


def hurtbox_active(hurtbox: dict[str, Any], frame: int) -> bool:
    start = int(hurtbox["active_start_frame"]) + int(hurtbox["invuln_frames"])
    end = int(hurtbox["active_end_frame"])
    return start <= frame <= end


def aabb_overlap(
    center_a: list[float],
    half_a: list[float],
    center_b: list[float],
    half_b: list[float],
) -> bool:
    for i in range(3):
        if abs(center_a[i] - center_b[i]) >= half_a[i] + half_b[i]:
            return False
    return True


def load_keyframes(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_entities(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pose_map(keyframes: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in keyframes:
        key = (row["entity_id"], row["bone"])
        out.setdefault(key, []).append(row)
    for frames in out.values():
        frames.sort(key=lambda r: int(r["frame"]))
    return out


def sample_pose(
    frames: list[dict[str, Any]],
    frame: int,
    *,
    use_slerp: bool = True,
) -> tuple[list[float], list[float], int]:
    if not frames:
        return [0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0], 0
    if frame <= int(frames[0]["frame"]):
        row = frames[0]
        return row["pos"], row["rot"], int(row["instance_id"])
    if frame >= int(frames[-1]["frame"]):
        row = frames[-1]
        return row["pos"], row["rot"], int(row["instance_id"])
    for idx in range(len(frames) - 1):
        left = frames[idx]
        right = frames[idx + 1]
        lf = int(left["frame"])
        rf = int(right["frame"])
        if lf <= frame <= rf:
            if rf == lf:
                return left["pos"], left["rot"], int(left["instance_id"])
            t = (frame - lf) / (rf - lf)
            pos = lerp3(left["pos"], right["pos"], t)
            if use_slerp:
                rot = quat_slerp(left["rot"], right["rot"], t)
            else:
                rot = quat_slerp(left["rot"], right["rot"], t)
            return pos, rot, int(left["instance_id"])
    row = frames[-1]
    return row["pos"], row["rot"], int(row["instance_id"])


def detect_hits_for_tick(
    entities: dict[str, Any],
    keyframes: list[dict[str, Any]],
    tick: int,
    tick_rate: int,
    fps: int,
    *,
    use_slerp: bool = True,
    apply_invuln: bool = True,
    dedup: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    frame = tick_to_frame(tick, tick_rate, fps)
    ts = tick_to_ms(tick, tick_rate)
    poses = pose_map(keyframes)
    hits: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    for ent in entities["entities"]:
        events.append(
            {
                "tick": tick,
                "frame": frame,
                "timestamp_ms": ts,
                "entity_id": ent["entity_id"],
                "bone": "",
                "event_type": "pose_sample",
            }
        )

    for attacker in entities["entities"]:
        if not attacker.get("hitboxes"):
            continue
        for hitbox in attacker["hitboxes"]:
            bone = hitbox["bone"]
            frames = poses.get((attacker["entity_id"], bone), [])
            pos, rot, instance_id = sample_pose(frames, frame, use_slerp=use_slerp)
            offset = rotate_vec_by_quat(hitbox["local_offset"], rot)
            hit_center = [pos[i] + offset[i] for i in range(3)]
            hit_half = hitbox["half_extents"]
            for defender in entities["entities"]:
                if defender["entity_id"] == attacker["entity_id"]:
                    continue
                if defender.get("team") == attacker.get("team"):
                    continue
                hb = defender["hurtbox"]
                active = (
                    int(hb["active_start_frame"]) <= frame <= int(hb["active_end_frame"])
                    if not apply_invuln
                    else hurtbox_active(hb, frame)
                )
                if not active:
                    continue
                if aabb_overlap(hit_center, hit_half, hb["center"], hb["half_extents"]):
                    hit = {
                        "tick": tick,
                        "frame": frame,
                        "timestamp_ms": ts,
                        "attacker_id": attacker["entity_id"],
                        "defender_id": defender["entity_id"],
                        "instance_id": instance_id,
                        "bone": bone,
                    }
                    hits.append(hit)
                    if not dedup:
                        hits.append(dict(hit))

    if dedup:
        seen: set[tuple[int, str, str, int]] = set()
        unique: list[dict[str, Any]] = []
        for hit in hits:
            key = (
                int(hit["tick"]),
                str(hit["attacker_id"]),
                str(hit["defender_id"]),
                int(hit["instance_id"]),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(hit)
        hits = unique

    return hits, events


def reference_tick_ledger(
    entities_path: Path,
    animation_path: Path,
    *,
    tick_rate: int,
    fps: int,
    max_tick: int,
) -> list[dict[str, Any]]:
    entities = load_entities(entities_path)
    keyframes = load_keyframes(animation_path)
    rows: list[dict[str, Any]] = []
    for tick in range(max_tick + 1):
        hits, events = detect_hits_for_tick(
            entities, keyframes, tick, tick_rate, fps
        )
        rows.append({"tick": tick, "hits": hits, "events": events})
    return rows


def finalize_report(report: dict[str, Any]) -> dict[str, Any]:
    report = dict(report)
    report["hits"] = sorted(
        report["hits"],
        key=lambda h: (
            h["tick"],
            h["defender_id"],
            h["instance_id"],
            h["attacker_id"],
        ),
    )
    report["events"] = sorted(
        report["events"],
        key=lambda e: (e["tick"], e["entity_id"]),
    )
    return report


def reference_replay(
    entities_path: Path,
    animation_path: Path,
    *,
    tick_rate: int,
    fps: int,
    max_tick: int,
) -> dict[str, Any]:
    rows = reference_tick_ledger(
        entities_path, animation_path, tick_rate=tick_rate, fps=fps, max_tick=max_tick
    )
    report: dict[str, Any] = {
        "layout_version": 1,
        "tick_rate": tick_rate,
        "anim_fps": fps,
        "hits": [],
        "events": [],
    }
    for row in rows:
        report["hits"].extend(row["hits"])
        report["events"].extend(row["events"])
    return finalize_report(report)


def mutate_invuln(entities: dict[str, Any], seed: str) -> dict[str, Any]:
    out = json.loads(json.dumps(entities))
    delta = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:2], 16) % 5
    for ent in out["entities"]:
        if ent["entity_id"] == "dummy":
            ent["hurtbox"]["invuln_frames"] = int(ent["hurtbox"]["invuln_frames"]) + delta - 2
    return out


def mutate_keyframe_timing(keyframes: list[dict[str, Any]], seed: str) -> list[dict[str, Any]]:
    delta = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[2:4], 16) % 3
    out: list[dict[str, Any]] = []
    for row in keyframes:
        k = dict(row)
        if int(k["frame"]) > 0:
            k["frame"] = int(k["frame"]) + delta
        out.append(k)
    return out
