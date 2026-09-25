"""Build CWRC component wire fixtures for component-gov."""

from __future__ import annotations

import struct
from pathlib import Path

MAGIC = b"CWRC"
VERSION = 1
KIND_FUNC = 1
KIND_INSTANCE = 2


def leb128_encode(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            b |= 0x80
        out.append(b)
        if not n:
            break
    return bytes(out)


def write_import(buf: bytearray, module: str, name: str, type_local: int) -> None:
    mb = module.encode()
    nb = name.encode()
    buf.append(len(mb))
    buf.extend(mb)
    buf.append(len(nb))
    buf.extend(nb)
    buf.extend(struct.pack("<H", type_local))


def encode_export(kind: int, name: str, instance_target: int | None = None) -> bytes:
    out = bytearray()
    out.append(kind)
    nb = name.encode()
    out.append(len(nb))
    out.extend(nb)
    if kind == KIND_INSTANCE and instance_target is not None:
        out.extend(struct.pack("<H", instance_target))
    return bytes(out)


def build_cwrc(
    imports: list[tuple[str, str, int]],
    aliases: list[tuple[int, int]],
    export_records: list[bytes],
    reexports: list[tuple[str, int, str]],
    *,
    export_leb_override: int | None = None,
) -> bytes:
    payload = b"".join(export_records)
    leb_len = export_leb_override if export_leb_override is not None else len(payload)
    buf = bytearray(MAGIC)
    buf.append(VERSION)
    buf.extend(struct.pack("<H", len(imports)))
    for module, name, tlocal in imports:
        write_import(buf, module, name, tlocal)
    buf.extend(struct.pack("<H", len(aliases)))
    for local, module_type in aliases:
        buf.extend(struct.pack("<HH", local, module_type))
    buf.extend(leb128_encode(leb_len))
    buf.extend(payload)
    buf.extend(struct.pack("<H", len(reexports)))
    for outer, via, inner in reexports:
        ob = outer.encode()
        ib = inner.encode()
        buf.append(len(ob))
        buf.extend(ob)
        buf.extend(struct.pack("<H", via))
        buf.append(len(ib))
        buf.extend(ib)
    return bytes(buf)


def write_fixtures(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    tuple_order = build_cwrc(
        imports=[("b", "y", 0), ("aa", "z", 1)],
        aliases=[],
        export_records=[encode_export(KIND_FUNC, "noop")],
        reexports=[],
    )
    (out_dir / "tuple_order.cwasm").write_bytes(tuple_order)

    alias_basic = build_cwrc(
        imports=[("env", "mem", 5)],
        aliases=[(5, 99)],
        export_records=[encode_export(KIND_FUNC, "run")],
        reexports=[],
    )
    (out_dir / "alias_basic.cwasm").write_bytes(alias_basic)

    chain_surface = build_cwrc(
        imports=[("host", "log", 0)],
        aliases=[],
        export_records=[
            encode_export(KIND_FUNC, "leaf"),
            encode_export(KIND_INSTANCE, "child", 0),
        ],
        reexports=[("surface", 1, "child")],
    )
    (out_dir / "chain_surface.cwasm").write_bytes(chain_surface)

    tb3_alias = build_cwrc(
        imports=[("wit", "bind", 3), ("aa", "core", 1)],
        aliases=[(3, 50), (1, 7)],
        export_records=[encode_export(KIND_FUNC, "entry")],
        reexports=[],
    )
    tb3_dir = Path(__file__).resolve().parent / "data"
    tb3_dir.mkdir(parents=True, exist_ok=True)
    (tb3_dir / "tb3_alias_heavy.cwasm").write_bytes(tb3_alias)

    tb3_chain = build_cwrc(
        imports=[("x", "a", 0)],
        aliases=[],
        export_records=[
            encode_export(KIND_FUNC, "terminal"),
            encode_export(KIND_INSTANCE, "hop", 0),
        ],
        reexports=[("api", 1, "hop")],
    )
    (tb3_dir / "tb3_chain_deep.cwasm").write_bytes(tb3_chain)

    tb3_span = build_cwrc(
        imports=[("host", "tick", 0)],
        aliases=[],
        export_records=[encode_export(KIND_FUNC, "spanned")],
        reexports=[],
        export_leb_override=200,
    )
    (tb3_dir / "tb3_span_overstated.cwasm").write_bytes(tb3_span)


if __name__ == "__main__":
    data = Path(__file__).resolve().parents[1] / "environment" / "data" / "components"
    write_fixtures(data)
    print(f"wrote fixtures under {data} and {Path(__file__).resolve().parent / 'data'}")
