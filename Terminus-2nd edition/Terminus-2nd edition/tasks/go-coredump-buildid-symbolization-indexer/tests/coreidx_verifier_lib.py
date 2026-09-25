"""Independent reference helpers for coredump build-ID symbolization verifier."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

APP = Path("/app")
DEFAULT_CATALOG = APP / "fixtures" / "catalog" / "build_index.json"


def catalog_integrity_ok(path: Path) -> bool:
    return path.is_file() and len(hashlib.sha256(path.read_bytes()).hexdigest()) == 64


def parse_hex(s: str) -> int:
    return int(s.lower().removeprefix("0x"), 16)


def read_build_id_from_elf(path: Path) -> str:
    data = path.read_bytes()
    if len(data) < 120 or data[:4] != b"\x7fELF":
        return ""
    # Minimal fixture ELFs place one PT_NOTE payload at file offset 0x200 (see build_fixtures.py).
    note_off = 0x200
    if note_off + 12 > len(data):
        return ""
    off = note_off
    while off + 12 <= len(data):
        namesz = struct.unpack_from("<I", data, off)[0]
        descsz = struct.unpack_from("<I", data, off + 4)[0]
        ntype = struct.unpack_from("<I", data, off + 8)[0]
        off += 12
        name_end = off + namesz
        desc_end = name_end + descsz
        if desc_end > len(data):
            break
        name = data[off:name_end]
        desc = data[name_end:desc_end]
        off = (desc_end + 3) & ~3
        if b"GNU" in name and ntype == 3 and desc:
            return desc.hex().upper()
    return ""


def locate_pc(pc_hex: str, mmaps: list[dict]) -> dict | None:
    pc = parse_hex(pc_hex)
    hits: list[tuple[int, dict]] = []
    for m in mmaps:
        start = parse_hex(m["start"])
        end = parse_hex(m["end"])
        foff = parse_hex(m["file_offset"])
        if start <= pc < end:
            hits.append((foff, m))
    if not hits:
        return None
    hits.sort(key=lambda x: x[0], reverse=True)
    return hits[0][1]


def lookup_symbol(catalog: dict, path: str, file_offset: int) -> str:
    entry = catalog["binaries"].get(path)
    if not entry:
        return ""
    if entry.get("stripped"):
        dbg = entry.get("debug_path", "")
        if dbg and dbg in catalog["binaries"]:
            entry = catalog["binaries"][dbg]
        else:
            alt = Path(path).parent / ".debug" / Path(path).name
            if str(alt) in catalog["binaries"]:
                entry = catalog["binaries"][str(alt)]
    best = ""
    for sym in sorted(entry.get("symbols", []), key=lambda s: s["offset"]):
        if sym["offset"] <= file_offset:
            best = sym["name"]
    return best


def dedupe_group_key(rec: dict, build_id: str, top_symbol: str) -> str:
    mod = ""
    if rec["threads"] and rec["threads"][0]["frames"]:
        mod = Path(rec["threads"][0]["frames"][0]["module"]).name
    payload = f"{build_id.upper()}:{rec['signal']}:{top_symbol}:{mod}"
    return hashlib.sha256(payload.encode()).hexdigest()


def reference_stage_rows(crashes: Path, catalog_path: Path) -> list[dict]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for fp in sorted(crashes.glob("*.crash.jsonl")):
        for line in fp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            top_pc = rec["threads"][0]["frames"][0]["pc"]
            hit = locate_pc(top_pc, rec["mmap"])
            build_id = read_build_id_from_elf(Path(hit["path"])) if hit else ""
            resolved = []
            for th in rec["threads"]:
                for fr in th["frames"]:
                    h = locate_pc(fr["pc"], rec["mmap"])
                    sym = ""
                    if h:
                        rel = parse_hex(fr["pc"]) - parse_hex(h["start"]) + parse_hex(h["file_offset"])
                        sym = lookup_symbol(catalog, h["path"], rel)
                    resolved.append({"pc": fr["pc"], "module": fr["module"], "symbol": sym})
            top_symbol = resolved[0]["symbol"] if resolved else ""
            rows.append(
                {
                    "crash_id": rec["crash_id"],
                    "timestamp": rec["timestamp"],
                    "signal": rec["signal"],
                    "pid": rec["pid"],
                    "group_key": dedupe_group_key(rec, build_id, top_symbol),
                    "build_id": build_id,
                    "top_symbol": top_symbol,
                    "frames": resolved,
                }
            )
    rows.sort(key=lambda r: (r["timestamp"], r["crash_id"]))
    return rows
