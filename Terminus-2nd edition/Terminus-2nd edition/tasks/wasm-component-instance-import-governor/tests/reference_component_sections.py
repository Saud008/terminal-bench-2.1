"""Independent reference CWRC component parser for component-gov."""

from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path
from typing import Any

MAGIC = b"CWRC"
KIND_FUNC = 1
KIND_INSTANCE = 2


def leb128_decode(raw: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    start = pos
    for _ in range(5):
        if pos >= len(raw):
            raise ValueError("leb128 eof")
        byte = raw[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if byte & 0x80 == 0:
            return result, pos - start
        shift += 7
    raise ValueError("leb128 overflow")


def parse_cwrc(raw: bytes) -> dict[str, Any]:
    if raw[:4] != MAGIC:
        raise ValueError("bad magic")
    pos = 5
    import_count = struct.unpack_from("<H", raw, pos)[0]
    pos += 2
    imports: list[dict[str, Any]] = []
    for _ in range(import_count):
        mlen = raw[pos]
        pos += 1
        module = raw[pos : pos + mlen].decode()
        pos += mlen
        nlen = raw[pos]
        pos += 1
        name = raw[pos : pos + nlen].decode()
        pos += nlen
        type_local = struct.unpack_from("<H", raw, pos)[0]
        pos += 2
        imports.append({"module": module, "name": name, "type_local": type_local})
    alias_count = struct.unpack_from("<H", raw, pos)[0]
    pos += 2
    aliases: list[dict[str, int]] = []
    for _ in range(alias_count):
        local = struct.unpack_from("<H", raw, pos)[0]
        pos += 2
        module_type = struct.unpack_from("<H", raw, pos)[0]
        pos += 2
        aliases.append({"local": local, "module_type": module_type})
    export_len, _ = leb128_decode(raw, pos)
    pos += _ if _ else 1
    payload_start = pos
    payload_end = payload_start + export_len
    if payload_end > len(raw):
        raise ValueError("export section length exceeds file")
    exports = decode_exports_guarded(raw[payload_start:payload_end], export_len)
    pos = payload_end
    re_count = struct.unpack_from("<H", raw, pos)[0]
    pos += 2
    reexports: list[dict[str, Any]] = []
    for _ in range(re_count):
        olen = raw[pos]
        pos += 1
        outer = raw[pos : pos + olen].decode()
        pos += olen
        via = struct.unpack_from("<H", raw, pos)[0]
        pos += 2
        ilen = raw[pos]
        pos += 1
        inner = raw[pos : pos + ilen].decode()
        pos += ilen
        reexports.append({"outer": outer, "via_instance": via, "inner": inner})
    if pos != len(raw):
        raise ValueError("trailing bytes")
    return {
        "imports": imports,
        "aliases": aliases,
        "exports": exports,
        "reexports": reexports,
    }


def decode_exports_guarded(payload: bytes, declared_len: int) -> list[dict[str, Any]]:
    if declared_len > len(payload):
        raise ValueError("export leb128 span invalid")
    body = payload[:declared_len]
    out: list[dict[str, Any]] = []
    pos = 0
    while pos < len(body):
        kind = body[pos]
        pos += 1
        nlen = body[pos]
        pos += 1
        name = body[pos : pos + nlen].decode()
        pos += nlen
        inst = None
        if kind == KIND_INSTANCE:
            inst = struct.unpack_from("<H", body, pos)[0]
            pos += 2
        out.append({"kind": kind, "name": name, "instance_target": inst})
    return out


def canonical_imports(imports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(imports, key=lambda r: (r["module"].encode(), r["name"].encode()))


def resolve_type_index(local: int, aliases: list[dict[str, int]]) -> int:
    for row in aliases:
        if row["local"] == local:
            return row["module_type"]
    return local


def tb3_offset(module_type: int) -> int:
    raw = os.environ.get("TB3_TYPE_ALIAS_OFFSET", "")
    if raw:
        return module_type + int(raw)
    return module_type


def import_reorder_digest(
    imports: list[dict[str, Any]], aliases: list[dict[str, int]]
) -> str:
    ordered = canonical_imports(imports)
    buf = bytearray()
    for row in ordered:
        module = row["module"].encode()
        name = row["name"].encode()
        buf.append(len(module))
        buf.extend(module)
        buf.append(len(name))
        buf.extend(name)
        mt = tb3_offset(resolve_type_index(row["type_local"], aliases))
        buf.extend(struct.pack("<H", mt))
    return hashlib.sha256(buf).hexdigest()


def _funcs_on(inst: int, exports: list[dict[str, Any]]) -> dict[str, str]:
    if inst != 0:
        return {}
    out: dict[str, str] = {}
    for exp in exports:
        if exp["kind"] == KIND_FUNC:
            out[exp["name"]] = exp["name"]
    return out


def _instance_links(exports: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for exp in exports:
        if exp["kind"] == KIND_INSTANCE and exp["instance_target"] is not None:
            out[exp["name"]] = int(exp["instance_target"])
    return out


def _resolve_symbol(
    inst: int,
    sym: str,
    exports: list[dict[str, Any]],
    reexports: list[dict[str, Any]],
    seen: set[tuple[int, str]],
) -> str | None:
    key = (inst, sym)
    if key in seen:
        return None
    seen.add(key)
    funcs = _funcs_on(inst, exports)
    if sym in funcs:
        return funcs[sym]
    links = _instance_links(exports)
    if sym in links:
        child = links[sym]
        leaf = _first_func(child, exports)
        if leaf:
            return leaf
    for edge in reexports:
        if edge["via_instance"] == inst and edge["outer"] == sym:
            return _resolve_symbol(inst, edge["inner"], exports, reexports, seen)
        if edge["via_instance"] == inst and edge["inner"] == sym:
            return _resolve_symbol(inst, edge["outer"], exports, reexports, seen)
    return None


def _first_func(inst: int, exports: list[dict[str, Any]]) -> str | None:
    funcs = _funcs_on(inst, exports)
    if funcs:
        return next(iter(sorted(funcs.values())))
    return None


def resolve_surfaces(parsed: dict[str, Any]) -> list[dict[str, str]]:
    exports = parsed["exports"]
    reexports = parsed["reexports"]
    out: list[dict[str, str]] = []
    for edge in reexports:
        leaf = _resolve_symbol(
            int(edge["via_instance"]), edge["inner"], exports, reexports, set()
        )
        if leaf:
            out.append({"outer": edge["outer"], "resolved_leaf": leaf})
    out.sort(key=lambda r: r["outer"])
    return out


def reference_attest_component(name: str, raw: bytes) -> dict[str, Any]:
    parsed = parse_cwrc(raw)
    ordered = canonical_imports(parsed["imports"])
    imports = [
        {
            "module": r["module"],
            "name": r["name"],
            "type_index": tb3_offset(
                resolve_type_index(r["type_local"], parsed["aliases"])
            ),
        }
        for r in ordered
    ]
    return {
        "name": name,
        "imports": imports,
        "surface_exports": resolve_surfaces(parsed),
        "import_reorder_digest": import_reorder_digest(
            parsed["imports"], parsed["aliases"]
        ),
    }


def reference_attest_dir(components_dir: Path) -> dict[str, Any]:
    names = sorted(p.name for p in components_dir.glob("*.cwasm"))
    components = []
    for name in names:
        raw = (components_dir / name).read_bytes()
        components.append(reference_attest_component(name, raw))
    return {"ingest_seq": 1, "components": components}


def load_attest_export(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
