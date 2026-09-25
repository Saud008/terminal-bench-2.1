"""Independent Avro compatibility reference math for verifier parity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_meta(raw: dict) -> tuple[str, str | None, list[str]]:
    name = raw.get("name", "Anonymous")
    namespace = raw.get("namespace")
    aliases = raw.get("aliases") or []
    return name, namespace, list(aliases)


def full_name(raw: dict) -> str:
    name, namespace, _ = schema_meta(raw)
    return f"{namespace}.{name}" if namespace else name


def type_label(v) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "union"
    if isinstance(v, dict):
        if "logicalType" in v:
            return f"logical:{v['logicalType']}"
        return str(v.get("type", "record"))
    return "unknown"


def union_branches(v) -> list[str] | None:
    if isinstance(v, list):
        return sorted(type_label(x) for x in v)
    if isinstance(v, dict) and v.get("type") == "array":
        return union_branches(v.get("items"))
    return None


def fields_map(raw: dict) -> dict[str, object]:
    out: dict[str, object] = {}
    if raw.get("type") != "record":
        return out
    for f in raw.get("fields") or []:
        out[f["name"]] = f.get("type")
    return out


def alias_equivalent(w: dict, r: dict) -> bool:
    wn, _, wa = schema_meta(w)
    rn, _, ra = schema_meta(r)
    if wn == rn:
        return True
    wf, rf = full_name(w), full_name(r)
    return wf == rf or wf in ra or rf in wa


def promotion_ok(wt, rt) -> bool:
    wl, rl = type_label(wt), type_label(rt)
    if wl == rl:
        return True
    return (wl, rl) in (("int", "long"), ("float", "double"))


def defaults_compatible(w: dict, r: dict) -> bool:
    wf = {f["name"]: f for f in w.get("fields") or []}
    for f in r.get("fields") or []:
        name = f["name"]
        if name in wf:
            continue
        if "default" not in f:
            return False
    return True


def field_promotions_ok(w: dict, r: dict) -> bool:
    wfm = fields_map(w)
    rfm = fields_map(r)
    for name, rt in rfm.items():
        if name in wfm and not promotion_ok(wfm[name], rt):
            return False
    return True


def union_fields_ok(w: dict, r: dict) -> bool:
    wfm = fields_map(w)
    rfm = fields_map(r)
    for name, wt in wfm.items():
        if name not in rfm:
            continue
        wb, rb = union_branches(wt), union_branches(rfm[name])
        if wb is None and rb is None:
            continue
        if wb is None or rb is None:
            return False
        if wb != rb:
            return False
    return True


def decimal_ok(wt: dict, rt: dict) -> bool:
    wp, ws = wt.get("precision", 0), wt.get("scale", 0)
    rp, rs = rt.get("precision", 0), rt.get("scale", 0)
    return wp <= rp and ws == rs


def logical_ok(w: dict, r: dict) -> bool:
    wfm = fields_map(w)
    rfm = fields_map(r)
    for name, rt in rfm.items():
        if name not in wfm:
            continue
        wt = wfm[name]
        if (
            type_label(wt).startswith("logical:decimal") or type_label(rt).startswith("logical:decimal")
        ) and not (isinstance(wt, dict) and isinstance(rt, dict) and decimal_ok(wt, rt)):
            return False

        def lname(v):
            return v.get("logicalType") if isinstance(v, dict) else None

        if (lname(wt) == "timestamp-millis" or lname(rt) == "timestamp-millis") and lname(wt) != lname(rt):
            return False
    return True


def canonicalize(v):
    if isinstance(v, dict):
        out = {}
        for k in sorted(v.keys()):
            if k in ("doc", "default", "aliases"):
                continue
            val = v[k]
            if k == "fields" and v.get("type") == "record" and isinstance(val, list):
                fields = [canonicalize(f) for f in val]
                fields.sort(key=lambda f: f.get("name", ""))
                out[k] = fields
            else:
                out[k] = canonicalize(val)
        return out
    if isinstance(v, list):
        return [canonicalize(x) for x in v]
    return v


def parsing_fingerprint(raw: dict) -> str:
    canon = canonicalize(raw)
    blob = json.dumps(canon, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def evaluate_pair(subject: str, writer_path: Path, reader_path: Path) -> dict:
    w = load_schema(writer_path)
    r = load_schema(reader_path)
    violations: list[str] = []
    namespace_alias_ok = alias_equivalent(w, r)
    if not namespace_alias_ok:
        violations.append("namespace_alias")
    defaults_ok = defaults_compatible(w, r) and field_promotions_ok(w, r)
    if not defaults_ok:
        violations.append("default_rules")
    union_order_ok = union_fields_ok(w, r)
    if not union_order_ok:
        violations.append("union_order")
    logical_types_ok = logical_ok(w, r)
    if not logical_types_ok:
        violations.append("logical_types")
    compatible = not violations
    return {
        "subject": subject,
        "writer_path": str(writer_path),
        "reader_path": str(reader_path),
        "writer_fingerprint": parsing_fingerprint(w),
        "reader_fingerprint": parsing_fingerprint(r),
        "compatible": compatible,
        "violations": violations,
        "checks": {
            "namespace_alias_ok": namespace_alias_ok,
            "defaults_ok": defaults_ok,
            "union_order_ok": union_order_ok,
            "logical_types_ok": logical_types_ok,
        },
    }


def classify_risk(row: dict) -> str:
    if row["compatible"]:
        return "low"
    if "logical_types" in row["violations"]:
        return "critical"
    if len(row["violations"]) >= 2:
        return "high"
    return "medium"


def reference_pair_ledger(schema_root: Path, pairs_path: Path) -> list[dict]:
    rows = []
    for line in pairs_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        spec = json.loads(line)
        row = evaluate_pair(
            spec["subject"],
            schema_root / spec["writer"],
            schema_root / spec["reader"],
        )
        rows.append(row)
    rows.sort(key=lambda r: r["subject"])
    return rows


def reference_migration_report(schema_root: Path, pairs_path: Path) -> dict:
    staging = reference_pair_ledger(schema_root, pairs_path)
    subjects = []
    compatible_count = 0
    high_risk = 0
    critical_risk = 0
    for row in staging:
        risk = classify_risk(row)
        if row["compatible"]:
            compatible_count += 1
        if risk == "high":
            high_risk += 1
        if risk == "critical":
            critical_risk += 1
        subjects.append(
            {
                "subject": row["subject"],
                "writer_fingerprint": row["writer_fingerprint"],
                "reader_fingerprint": row["reader_fingerprint"],
                "compatible": row["compatible"],
                "risk_level": risk,
                "violation_count": len(row["violations"]),
                "violations": row["violations"],
            }
        )
    subjects.sort(key=lambda s: s["subject"])
    return {
        "subjects": subjects,
        "totals": {
            "pair_count": len(subjects),
            "compatible_count": compatible_count,
            "high_risk_count": high_risk,
            "critical_risk_count": critical_risk,
        },
    }
