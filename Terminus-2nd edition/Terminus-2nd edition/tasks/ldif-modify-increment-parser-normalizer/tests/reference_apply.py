"""Independent LDIF apply reference (golden semantics)."""

from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Any


def seed_token(seed: str, label: str) -> str:
    hash_val = 0xCBF29CE484222325
    for byte in f"{seed}:{label}".encode("utf-8"):
        hash_val ^= byte
        hash_val = (hash_val * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{hash_val & 0xFFFF:04x}"


def substitute_seed(text: str, seed: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return seed_token(seed, match.group(1))

    return re.sub(r"\{\{SEED:([a-zA-Z0-9_]+)\}\}", repl, text)


def unfold_lines(raw: str) -> list[str]:
    out: list[str] = []
    for line in raw.splitlines():
        if line.startswith(" ") and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def split_line(line: str) -> tuple[str, str, bool]:
    if "::" in line:
        key, value = line.split("::", 1)
        return key.strip(), value.lstrip(), True
    if ":" in line:
        key, value = line.split(":", 1)
        return key.strip(), value.lstrip(), False
    raise ValueError(f"invalid line: {line}")


def decode_value(base64_flag: bool, value: str) -> str:
    if not base64_flag:
        return value
    padded = value.strip()
    while len(padded) % 4 != 0:
        padded += "="
    return base64.standard_b64decode(padded.encode("ascii")).decode("utf-8")


def parse_modify_op(lines: list[str], kind: str, attr_raw: str) -> tuple[dict[str, Any], int]:
    attr = attr_raw.strip().lower()
    values: list[str] = []
    consumed = 1
    while consumed < len(lines):
        line = lines[consumed]
        if line.strip() == "-":
            break
        key, value, b64 = split_line(line)
        if key.lower() != attr:
            break
        values.append(decode_value(b64, value))
        consumed += 1
    return {"kind": kind, "attr": attr, "values": values}, consumed


def parse_block(lines: list[str]) -> dict[str, Any]:
    dn = ""
    changetype = ""
    attributes: dict[str, list[str]] = {}
    modify_ops: list[dict[str, Any]] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if line.strip() == "-":
            idx += 1
            continue
        key, value, b64 = split_line(line)
        key_lower = key.lower()
        if key_lower == "dn" and not dn:
            dn = value
        elif key_lower == "changetype" and not changetype:
            changetype = value.lower()
        elif changetype == "modify" and key_lower in {"add", "delete", "replace"}:
            op, consumed = parse_modify_op(lines[idx:], key_lower, value)
            modify_ops.append(op)
            idx += consumed
            continue
        else:
            decoded = decode_value(b64, value)
            attributes.setdefault(key.lower(), []).append(decoded)
        idx += 1
    if not dn or not changetype:
        raise ValueError("missing dn or changetype")
    return {
        "dn": dn,
        "changetype": changetype,
        "attributes": attributes,
        "modify_ops": modify_ops,
    }


def parse_ldif(raw: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    block: list[str] = []
    for line in unfold_lines(raw):
        if not line.strip():
            if block:
                records.append(parse_block(block))
                block = []
            continue
        block.append(line)
    if block:
        records.append(parse_block(block))
    return records


def sort_attr_values(attrs: dict[str, list[str]]) -> dict[str, list[str]]:
    return {key: sorted(values) for key, values in sorted(attrs.items())}


def normalize_attrs(attrs: dict[str, list[str]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for key, values in attrs.items():
        out.setdefault(key.lower(), []).extend(values)
    return sort_attr_values(out)


def apply_modify_op(entry: dict[str, list[str]], op: dict[str, Any]) -> None:
    attr = op["attr"]
    kind = op["kind"]
    values = op["values"]
    if kind == "add":
        slot = entry.setdefault(attr, [])
        for value in values:
            if value not in slot:
                slot.append(value)
    elif kind == "replace":
        entry[attr] = list(values)
    elif kind == "delete":
        if not values:
            entry.pop(attr, None)
        elif attr in entry:
            entry[attr] = [v for v in entry[attr] if v not in values]
            if not entry[attr]:
                entry.pop(attr)


def apply_records(seed: str, records: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    directory: dict[str, dict[str, list[str]]] = {}
    audit_rows: list[dict[str, Any]] = []
    seq = 0
    applied = 0
    skipped = 0
    for record in records:
        ctype = record["changetype"]
        dn = record["dn"]
        if ctype == "add":
            directory[dn] = normalize_attrs(record["attributes"])
            seq += 1
            audit_rows.append(
                {"seq": seq, "dn": dn, "changetype": "add", "detail": "add"}
            )
            applied += 1
        elif ctype == "delete":
            directory.pop(dn, None)
            seq += 1
            audit_rows.append(
                {"seq": seq, "dn": dn, "changetype": "delete", "detail": "delete"}
            )
            applied += 1
        elif ctype == "modify":
            entry = directory.get(dn)
            if entry is None:
                skipped += 1
                continue
            for op in record["modify_ops"]:
                apply_modify_op(entry, op)
            seq += 1
            audit_rows.append(
                {
                    "seq": seq,
                    "dn": dn,
                    "changetype": "modify",
                    "detail": f"modify:{len(record['modify_ops'])}",
                }
            )
            applied += 1
    export_doc = {
        "seed": seed,
        "stats": {
            "records_total": len(records),
            "records_applied": applied,
            "records_skipped": skipped,
        },
        "entries": [
            {"dn": dn, "attributes": sort_attr_values(attrs)}
            for dn, attrs in sorted(directory.items())
        ],
    }
    return export_doc, audit_rows


def materialize_ldif_fixture(path: Path, seed: str) -> str:
    raw = path.read_text(encoding="utf-8")
    return substitute_seed(raw, seed)


def expect_ldif_directory(path: Path | str, seed: str) -> dict[str, Any]:
    text = materialize_ldif_fixture(Path(path), seed)
    records = parse_ldif(text)
    export_doc, _audit = apply_records(seed, records)
    return export_doc


def expect_ldif_audit_trail(path: Path | str, seed: str) -> dict[str, Any]:
    text = materialize_ldif_fixture(Path(path), seed)
    records = parse_ldif(text)
    _export, audit_rows = apply_records(seed, records)
    return {"seed": seed, "operations": audit_rows}


def materialize_ldif(path: Path, seed: str) -> str:
    return materialize_ldif_fixture(path, seed)


def reference_apply(path: Path | str, seed: str) -> dict[str, Any]:
    return expect_ldif_directory(path, seed)


def reference_audit(path: Path | str, seed: str) -> dict[str, Any]:
    return expect_ldif_audit_trail(path, seed)
