"""Independent reference for ecs-migrate apply — mirrors /app/docs contracts."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import struct
from pathlib import Path
from typing import Any

CHUNK_MAGIC = 0x45435331
STRIDE_V2 = 14


def load_layout(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def component_stride(manifest: dict[str, Any]) -> int:
    return max(c["offset"] + c["size"] for c in manifest["components"])


def signature_for_payload(manifest: dict[str, Any], payload: bytes) -> str:
    stride = component_stride(manifest)
    names: list[str] = []
    for comp in manifest["components"]:
        start = comp["offset"]
        end = start + comp["size"]
        if end <= stride and end <= len(payload) and any(payload[start:end]):
            names.append(comp["name"])
    names.sort()
    return "+".join(names)


def chunk_path(chunks_dir: Path, chunk_id: int) -> Path:
    return chunks_dir / f"chunk_{chunk_id:04d}.bin"


def read_chunk(chunks_dir: Path, chunk_id: int) -> tuple[int, list[dict[str, Any]]]:
    raw = chunk_path(chunks_dir, chunk_id).read_bytes()
    magic, file_id, layout_version, payload_len = struct.unpack(">IIII", raw[:16])
    if magic != CHUNK_MAGIC:
        raise ValueError("bad chunk magic")
    payload = raw[16 : 16 + payload_len]
    stride = STRIDE_V2 if layout_version >= 2 else 12
    record = 4 + stride
    entities: list[dict[str, Any]] = []
    off = 0
    while off + record <= len(payload):
        stable_id = struct.unpack(">I", payload[off : off + 4])[0]
        body = payload[off + 4 : off + record]
        entities.append({"stable_id": stable_id, "payload": bytes(body)})
        off += record
    return file_id, entities


def write_chunk(
    chunks_dir: Path,
    chunk_id: int,
    layout_version: int,
    manifest: dict[str, Any],
    entities: list[dict[str, Any]],
) -> None:
    stride = component_stride(manifest)
    payload = bytearray()
    for ent in entities:
        payload.extend(struct.pack(">I", ent["stable_id"]))
        body = bytearray(ent["payload"])
        body.extend(b"\x00" * max(0, stride - len(body)))
        payload.extend(bytes(body[:stride]))
    header = struct.pack(">IIII", CHUNK_MAGIC, chunk_id, layout_version, len(payload))
    chunk_path(chunks_dir, chunk_id).write_bytes(header + bytes(payload))


def list_chunk_ids(chunks_dir: Path) -> list[int]:
    ids: list[int] = []
    if not chunks_dir.is_dir():
        return ids
    for path in chunks_dir.glob("chunk_*.bin"):
        stem = path.stem
        ids.append(int(stem.split("_")[1]))
    return sorted(ids)


def chunk_checksum(chunk_id: int, layout_version: int, payload: bytes) -> str:
    prefix = struct.pack(">IIII", CHUNK_MAGIC, chunk_id, layout_version, len(payload))
    return hashlib.sha256(prefix + payload).hexdigest()


def load_journal(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def replay_start_cursor(journal: dict[str, Any]) -> int:
    if journal.get("status") == "committed":
        return max((e["step_order"] for e in journal["entries"]), default=0)
    return int(journal.get("commit_cursor", 0))


def ordered_steps(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    steps = list(manifest["migration_steps"])
    steps.sort(key=lambda s: s["order"])
    return steps


def apply_steps(
    conn: sqlite3.Connection,
    chunks_dir: Path,
    manifest: dict[str, Any],
    start_from: int,
) -> tuple[list[tuple[int, str, str, int]], int]:
    steps = ordered_steps(manifest)
    applied: list[tuple[int, str, str, int]] = []
    moved = 0
    stride_v2 = component_stride(manifest)
    for step in [s for s in steps if s["order"] > start_from]:
        touched: dict[int, int] = {}
        for chunk_id in list_chunk_ids(chunks_dir):
            if step["op"] == "move" and step.get("target_chunk") == chunk_id:
                continue
            _, entities = read_chunk(chunks_dir, chunk_id)
            changed = False
            if step["op"] == "add":
                comp = next(c for c in manifest["components"] if c["name"] == step["component"])
                for ent in entities:
                    body = bytearray(ent["payload"])
                    body.extend(b"\x00" * max(0, stride_v2 - len(body)))
                    if comp.get("default_hex"):
                        hex_bytes = bytes.fromhex(comp["default_hex"].removeprefix("0x"))
                        start = comp["offset"]
                        for i, b in enumerate(hex_bytes):
                            if start + i < len(body):
                                body[start + i] = b
                    ent["payload"] = bytes(body[:stride_v2])
                    changed = True
            elif step["op"] == "move":
                target = step["target_chunk"]
                from_sig = step["from_archetype"]
                keep = [
                    e
                    for e in entities
                    if signature_for_payload(manifest, e["payload"]) != from_sig
                ]
                moving = [
                    e
                    for e in entities
                    if signature_for_payload(manifest, e["payload"]) == from_sig
                ]
                if moving:
                    _, target_ents = read_chunk(chunks_dir, target)
                    start_slot = len(target_ents)
                    target_ents.extend(moving)
                    write_chunk(
                        chunks_dir, target, manifest["to_version"], manifest, target_ents
                    )
                    write_chunk(
                        chunks_dir, chunk_id, manifest["to_version"], manifest, keep
                    )
                    for new_slot, ent in enumerate(keep):
                        conn.execute(
                            "UPDATE entities SET slot = ? WHERE stable_id = ?",
                            (new_slot, ent["stable_id"]),
                        )
                    for offset, ent in enumerate(moving):
                        conn.execute(
                            "UPDATE entities SET chunk_id = ?, slot = ? WHERE stable_id = ?",
                            (target, start_slot + offset, ent["stable_id"]),
                        )
                    moved += len(moving)
                    changed = True
                    entities = keep
            if changed:
                touched[chunk_id] = touched.get(chunk_id, 0) + 1
                if step["op"] != "move":
                    write_chunk(
                        chunks_dir, chunk_id, manifest["to_version"], manifest, entities
                    )
        applied.append((step["order"], step["op"], step["component"], len(touched)))
    conn.commit()
    return applied, moved


def rebuild_archetypes(
    conn: sqlite3.Connection,
    manifest: dict[str, Any],
    chunks_dir: Path,
) -> None:
    stride = component_stride(manifest)
    payload_by_slot: dict[tuple[int, int], bytes] = {}
    for chunk_id in list_chunk_ids(chunks_dir):
        _, entities = read_chunk(chunks_dir, chunk_id)
        for slot, ent in enumerate(entities):
            body = bytearray(ent["payload"])
            body.extend(b"\x00" * max(0, stride - len(body)))
            payload_by_slot[(chunk_id, slot)] = bytes(body[:stride])

    rows = conn.execute(
        "SELECT stable_id, chunk_id, slot FROM entities WHERE alive = 1 ORDER BY stable_id ASC"
    ).fetchall()
    sig_to_id: dict[str, int] = {}
    next_id = 1
    counts: dict[int, int] = {}
    sig_by_id: dict[int, str] = {}
    for stable_id, chunk_id, slot in rows:
        payload = payload_by_slot.get((chunk_id, slot), bytes(stride))
        sig = signature_for_payload(manifest, payload)
        if sig in sig_to_id:
            archetype_id = sig_to_id[sig]
        else:
            archetype_id = next_id
            sig_to_id[sig] = archetype_id
            sig_by_id[archetype_id] = sig
            next_id += 1
        conn.execute(
            "UPDATE entities SET archetype_id = ? WHERE stable_id = ?",
            (archetype_id, stable_id),
        )
        counts[archetype_id] = counts.get(archetype_id, 0) + 1

    conn.execute("DELETE FROM archetypes")
    for archetype_id in sorted(counts):
        conn.execute(
            "INSERT INTO archetypes (archetype_id, signature, entity_count) VALUES (?,?,?)",
            (archetype_id, sig_by_id[archetype_id], counts[archetype_id]),
        )
    conn.commit()


def remap_entity_ids(conn: sqlite3.Connection) -> int:
    tombstones = {
        row[0]
        for row in conn.execute("SELECT stable_id FROM tombstones ORDER BY stable_id")
    }
    max_id = conn.execute("SELECT COALESCE(MAX(stable_id), 0) FROM entities").fetchone()[0]
    rowids = [
        row[0]
        for row in conn.execute(
            "SELECT rowid FROM entities WHERE alive = 1 AND stable_id = 0 ORDER BY rowid ASC"
        )
    ]
    remapped = 0
    next_id = max_id + 1
    for rowid in rowids:
        while next_id in tombstones:
            next_id += 1
        conn.execute("UPDATE entities SET stable_id = ? WHERE rowid = ?", (next_id, rowid))
        remapped += 1
        next_id += 1
    conn.commit()
    return remapped


def build_report(
    conn: sqlite3.Connection,
    manifest: dict[str, Any],
    chunks_dir: Path,
    applied: list[tuple[int, str, str, int]],
    moved: int,
    ids_remapped: int,
    replay_from: int,
) -> dict[str, Any]:
    steps_applied = [
        {
            "order": order,
            "op": op,
            "component": component,
            "chunks_touched": touched,
        }
        for order, op, component, touched in applied
    ]
    archetypes = [
        {
            "archetype_id": row[0],
            "signature": row[1],
            "entity_count": row[2],
        }
        for row in conn.execute(
            "SELECT archetype_id, signature, entity_count FROM archetypes ORDER BY archetype_id"
        )
    ]
    chunks: list[dict[str, Any]] = []
    for chunk_id in list_chunk_ids(chunks_dir):
        _, entities = read_chunk(chunks_dir, chunk_id)
        stride = component_stride(manifest)
        payload = bytearray()
        for ent in entities:
            payload.extend(struct.pack(">I", ent["stable_id"]))
            body = bytearray(ent["payload"])
            body.extend(b"\x00" * max(0, stride - len(body)))
            payload.extend(bytes(body[:stride]))
        raw_payload = bytes(payload)
        chunks.append(
            {
                "chunk_id": chunk_id,
                "checksum": chunk_checksum(chunk_id, manifest["to_version"], raw_payload),
                "entity_count": len(entities),
            }
        )
    return {
        "layout_id": manifest["layout_id"],
        "layout_version": manifest["to_version"],
        "steps_applied": steps_applied,
        "archetypes": archetypes,
        "chunks": chunks,
        "entities_moved": moved,
        "ids_remapped": ids_remapped,
        "journal_replayed_from": replay_from,
    }


def mark_committed(journal_path: Path, journal: dict[str, Any]) -> None:
    updated = dict(journal)
    updated["status"] = "committed"
    updated["commit_cursor"] = max((e["step_order"] for e in journal["entries"]), default=0)
    journal_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")


def reference_apply(
    db_path: Path,
    chunks_dir: Path,
    layout_path: Path,
    journal_path: Path,
) -> dict[str, Any]:
    manifest = load_layout(layout_path)
    journal = load_journal(journal_path)
    replay_from = replay_start_cursor(journal)
    work_db = db_path
    work_chunks = chunks_dir
    work_journal = journal_path
    conn = sqlite3.connect(work_db)
    try:
        applied, moved = apply_steps(conn, work_chunks, manifest, replay_from)
        if applied:
            rebuild_archetypes(conn, manifest, work_chunks)
            ids_remapped = remap_entity_ids(conn)
        else:
            ids_remapped = 0
        report = build_report(
            conn, manifest, work_chunks, applied, moved, ids_remapped, replay_from
        )
        conn.execute(
            """
            INSERT INTO migration_state (id, layout_version, journal_status, commit_cursor)
            VALUES (1, ?, 'committed', ?)
            ON CONFLICT(id) DO UPDATE SET
              layout_version = excluded.layout_version,
              journal_status = excluded.journal_status,
              commit_cursor = excluded.commit_cursor
            """,
            (
                manifest["to_version"],
                max((e["step_order"] for e in journal["entries"]), default=0),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    mark_committed(work_journal, journal)
    return report


def copy_fixture_tree(src_db: Path, src_chunks: Path, src_journal: Path, dest_root: Path) -> tuple[Path, Path, Path]:
    dest_root.mkdir(parents=True, exist_ok=True)
    db = dest_root / "ecs_meta.db"
    chunks = dest_root / "chunks"
    journal = dest_root / "replay.journal.json"
    shutil.copy2(src_db, db)
    if chunks.exists():
        shutil.rmtree(chunks)
    shutil.copytree(src_chunks, chunks)
    shutil.copy2(src_journal, journal)
    return db, chunks, journal
