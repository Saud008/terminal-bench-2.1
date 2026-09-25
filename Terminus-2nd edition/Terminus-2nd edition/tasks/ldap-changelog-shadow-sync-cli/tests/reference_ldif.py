"""Independent LDIF changelog reference for shadow-sync verifier."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ModifyOp:
    op: str
    attr: str
    values: list[str] = field(default_factory=list)


@dataclass
class Record:
    dn: str
    changetype: str
    change_number: int
    usn_changed: int
    attrs: dict[str, str] = field(default_factory=dict)
    modify_ops: list[ModifyOp] = field(default_factory=list)


@dataclass
class IngestStats:
    new_usns: int = 0
    replay_noop: int = 0


def normalize_dn(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    parts = _split_rdn(raw)
    out_parts = []
    for part in parts:
        eq = _index_unescaped_equals(part)
        if eq < 0:
            out_parts.append(part.lower())
            continue
        attr = part[:eq].strip().lower()
        val = part[eq + 1 :].strip()
        out_parts.append(f"{attr}={val}")
    return ",".join(out_parts)


def _split_rdn(dn: str) -> list[str]:
    parts: list[str] = []
    start = 0
    i = 0
    while i < len(dn):
        if dn[i] == "\\":
            i += 2
            continue
        if dn[i] == ",":
            parts.append(dn[start:i])
            start = i + 1
        i += 1
    parts.append(dn[start:])
    return parts


def _index_unescaped_equals(s: str) -> int:
    i = 0
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == "=":
            return i
        i += 1
    return -1


def canon_attrs(attrs: dict[str, str]) -> dict[str, str]:
    return {k.lower(): v for k, v in attrs.items()}


def parse_ldif(text: str) -> list[Record]:
    records: list[Record] = []
    cur: Record | None = None
    for line in text.replace("\r\n", "\n").split("\n"):
        if line == "":
            continue
        if line == "-":
            if cur is not None:
                records.append(cur)
                cur = None
            continue
        if cur is None:
            cur = Record(dn="", changetype="", change_number=0, usn_changed=0)
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        lk = key.lower()
        if lk == "dn":
            cur.dn = val
        elif lk == "changetype":
            cur.changetype = val.lower()
        elif lk == "changenumber":
            cur.change_number = int(val)
        elif lk == "usnchanged":
            cur.usn_changed = int(val)
        elif lk in ("add", "delete", "replace"):
            cur.modify_ops.append(ModifyOp(op=lk, attr=val.lower()))
        elif cur.modify_ops:
            cur.modify_ops[-1].values.append(val)
        else:
            cur.attrs[key.lower()] = val
    if cur is not None:
        records.append(cur)
    records.sort(key=lambda r: r.change_number)
    return records


def parse_ldif_file(path: Path) -> list[Record]:
    return parse_ldif(path.read_text(encoding="utf-8"))


def apply_modify(attrs: dict[str, str], ops: list[ModifyOp]) -> dict[str, str]:
    out = dict(attrs)
    for op in ops:
        attr = op.attr.lower()
        if op.op == "add" and op.values:
            out[attr] = op.values[0]
        elif op.op == "delete":
            out.pop(attr, None)
        elif op.op == "replace":
            out.pop(attr, None)
            if op.values:
                out[attr] = op.values[0]
    return out


def ingest_reference(
    records: list[Record], seen_usns: set[int] | None = None
) -> tuple[dict[str, dict[str, str]], list[dict], IngestStats]:
    if seen_usns is None:
        seen_usns = set()
    shadow: dict[str, dict[str, str]] = {}
    staging: list[dict] = []
    stats = IngestStats()
    ordered = sorted(records, key=lambda r: r.change_number)
    for rec in ordered:
        norm = normalize_dn(rec.dn)
        if rec.usn_changed in seen_usns:
            stats.replay_noop += 1
            continue
        stats.new_usns += 1
        seen_usns.add(rec.usn_changed)
        row: dict = {
            "normalized_dn": norm,
            "change_number": rec.change_number,
            "usn_changed": rec.usn_changed,
            "changetype": rec.changetype,
        }
        if rec.changetype == "add":
            shadow[norm] = canon_attrs(rec.attrs)
            row["attrs"] = dict(shadow[norm])
        elif rec.changetype == "delete":
            shadow.pop(norm, None)
        elif rec.changetype == "modify":
            base = dict(shadow.get(norm, {}))
            ops = [
                ModifyOp(op=op.op, attr=op.attr.lower(), values=list(op.values))
                for op in rec.modify_ops
            ]
            shadow[norm] = apply_modify(base, ops)
            row["attrs"] = dict(shadow[norm])
            row["modify_ops"] = [
                {"op": op.op, "attr": op.attr, "values": list(op.values)} for op in ops
            ]
        staging.append(row)
    return shadow, staging, stats


def build_shadow_doc(shadow: dict[str, dict[str, str]], usn_by_dn: dict[str, int]) -> dict:
    entries = []
    for dn in sorted(shadow):
        entries.append(
            {
                "normalized_dn": dn,
                "attrs": dict(shadow[dn]),
                "usn_changed": usn_by_dn.get(dn, 0),
            }
        )
    return {"entries": entries, "entry_count": len(entries)}


def build_audit_doc(
    shadow: dict[str, dict[str, str]],
    staging_lines: int,
    max_usn: int,
    export_sequence: int,
    stats: IngestStats,
) -> dict:
    return {
        "unique_dn_count": len(shadow),
        "changelog_lines_applied": staging_lines,
        "max_usn": max_usn,
        "export_sequence": export_sequence,
        "replay_stats": {
            "new_usns": stats.new_usns,
            "replay_noop": stats.replay_noop,
        },
    }


def max_applied_usn(records: list[Record], applied: set[int] | None = None) -> int:
    """Max uSNChanged among applied USNs (includes deleted entries)."""
    if applied is not None:
        return max(applied) if applied else 0
    if not records:
        return 0
    return max(r.usn_changed for r in records)


def max_usn_from_shadow(shadow: dict[str, dict[str, str]], records: list[Record]) -> int:
    """Deprecated alias: prefer max_applied_usn for audit expectations."""
    return max_applied_usn(records)


def rewrite_base_dn(text: str, suffix: str) -> str:
    """Replace dc=example,dc=com with per-test suffix."""
    return re.sub(
        r"dc=example,dc=com",
        f"dc={suffix},dc=local",
        text,
        flags=re.IGNORECASE,
    )


def build_case_collision_ldif(suffix: str) -> str:
    base = f"dc={suffix},dc=local"
    return f"""dn: CN=Case User,OU=People,{base}
changetype: add
changeNumber: 1
uSNChanged: 900
objectClass: person
cn: Case User
mail: case@example.com
-
dn: cn=Case User,ou=People,{base}
changetype: modify
changeNumber: 2
uSNChanged: 901
replace: mail
mail: CASE@example.com
-
"""


def ingest_file_reference(path: Path, seen_usns: set[int] | None = None) -> tuple[
    dict[str, dict[str, str]], list[dict], IngestStats
]:
    return ingest_reference(parse_ldif_file(path), seen_usns)
