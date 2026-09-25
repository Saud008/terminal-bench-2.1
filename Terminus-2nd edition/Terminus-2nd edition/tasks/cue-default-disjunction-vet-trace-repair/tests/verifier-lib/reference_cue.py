"""Independent CUE DSL parser and evaluator for cuectl verifier."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FieldSpec:
    name: str
    optional: bool
    typ: str
    disjuncts: list[str] = field(default_factory=list)


@dataclass
class SchemaSpec:
    name: str
    closed: bool = False
    embed: str = ""
    fields: list[FieldSpec] = field(default_factory=list)
    file: str = ""
    line: int = 0


@dataclass
class ConfigValue:
    literal: str = ""
    use_disjunct: bool = False
    file: str = ""
    line: int = 0


@dataclass
class ConfigSpec:
    id: str
    schema: str
    fields: dict[str, ConfigValue] = field(default_factory=dict)
    file: str = ""
    line: int = 0


@dataclass
class VetRule:
    path: str
    attr: str
    file: str = ""
    line: int = 0


@dataclass
class ExportRule:
    path: str
    kind: str
    file: str = ""
    line: int = 0


@dataclass
class Workspace:
    name: str
    dir: Path
    includes: list[str]
    schemas: dict[str, SchemaSpec]
    configs: dict[str, ConfigSpec]
    vet_rules: list[VetRule]
    exports: list[ExportRule]


@dataclass
class FlatSchema:
    chain: list[str]
    fields: dict[str, FieldSpec]
    closed: bool


def fnv1a64(seed: str) -> int:
    h = 0xCBF29CE484222325
    for b in seed.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def default_disjunct_index(seed: str, count: int) -> int:
    if count <= 0:
        return 0
    return fnv1a64(seed) % count


def resolve_disjunct_value(seed: str, opts: list[str]) -> str:
    if not opts:
        return ""
    return opts[default_disjunct_index(seed, len(opts))]


def split_lines(text: str) -> list[str]:
    return text.replace("\r\n", "\n").split("\n")


def unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def parse_manifest(text: str) -> list[str]:
    for line in split_lines(text):
        line = line.strip()
        if line.startswith("include"):
            start = line.index("[")
            end = line.index("]")
            inner = line[start + 1 : end]
            return [unquote(p.strip()) for p in inner.split(",") if p.strip()]
    raise ValueError("workspace include missing")


def parse_field_decl(line: str) -> FieldSpec:
    parts = line.split()
    if len(parts) < 2:
        raise ValueError(f"invalid field {line!r}")
    name = parts[0]
    optional = name.endswith("?")
    if optional:
        name = name[:-1]
    typ = parts[1]
    if typ == "disjunct":
        return FieldSpec(name=name, optional=optional, typ=typ, disjuncts=parts[2:])
    if typ in ("string", "int"):
        return FieldSpec(name=name, optional=optional, typ=typ)
    raise ValueError(f"unknown type {typ}")


def parse_schema(lines: list[str], start: int, file: str) -> tuple[SchemaSpec, int]:
    line = lines[start].strip()
    open_idx = line.index("{")
    header = line[:open_idx].strip()
    parts = header.split()
    if len(parts) != 2:
        raise ValueError("invalid schema header")
    spec = SchemaSpec(name=parts[1], file=file, line=start + 1)
    i = start
    if not line.rstrip().endswith("}"):
        i += 1
        while i < len(lines):
            body = lines[i].strip()
            i += 1
            if body == "}":
                break
            if body == "closed":
                spec.closed = True
                continue
            if body.startswith("embed "):
                spec.embed = body[len("embed ") :].strip()
                continue
            spec.fields.append(parse_field_decl(body))
    return spec, i


def parse_config(lines: list[str], start: int, file: str) -> tuple[ConfigSpec, int]:
    line = lines[start].strip()
    open_idx = line.index("{")
    header = line[:open_idx].strip()
    if not header.startswith("config "):
        raise ValueError("invalid config header")
    rest = header[len("config ") :].strip()
    cfg_id, schema = [p.strip() for p in rest.split(":", 1)]
    spec = ConfigSpec(id=cfg_id, schema=schema, file=file, line=start + 1)
    i = start
    if not line.rstrip().endswith("}"):
        i += 1
        while i < len(lines):
            body = lines[i].strip()
            line_num = i + 1
            i += 1
            if body == "}":
                break
            parts = body.split()
            if len(parts) < 2:
                raise ValueError("invalid config field")
            name = parts[0]
            val = ConfigValue(file=file, line=line_num)
            if parts[1] == "disjunct":
                val.use_disjunct = True
            else:
                val.literal = unquote(" ".join(parts[1:]))
            spec.fields[name] = val
    return spec, i


def parse_file(ws: Workspace, file: str, text: str) -> None:
    lines = split_lines(text)
    i = 0
    while i < len(lines):
        line_num = i + 1
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("//"):
            continue
        if line.startswith("schema "):
            spec, i = parse_schema(lines, i - 1, file)
            ws.schemas[spec.name] = spec
            continue
        if line.startswith("config "):
            spec, i = parse_config(lines, i - 1, file)
            ws.configs[spec.id] = spec
            continue
        if line.startswith("vet "):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"line {line_num}: invalid vet rule")
            ws.vet_rules.append(VetRule(path=parts[1], attr=parts[2], file=file, line=line_num))
            continue
        if line.startswith("export "):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"line {line_num}: invalid export rule")
            ws.exports.append(ExportRule(path=parts[1], kind=parts[2], file=file, line=line_num))
            continue
        raise ValueError(f"line {line_num}: unknown statement")


def load_workspace(directory: Path) -> Workspace:
    manifest = (directory / "workspace.cue").read_text(encoding="utf-8")
    includes = parse_manifest(manifest)
    ws = Workspace(
        name=directory.name,
        dir=directory,
        includes=includes,
        schemas={},
        configs={},
        vet_rules=[],
        exports=[],
    )
    for rel in includes:
        parse_file(ws, rel, (directory / rel).read_text(encoding="utf-8"))
    return ws


def flatten_schema(ws: Workspace, name: str, seen: dict[str, bool] | None = None) -> FlatSchema:
    if seen is None:
        seen = {}
    if seen.get(name):
        raise ValueError("embed cycle")
    seen[name] = True
    spec = ws.schemas.get(name)
    if spec is None:
        raise ValueError(f"unknown schema {name}")
    chain = [name]
    fields = {f.name: f for f in spec.fields}
    closed = spec.closed
    if spec.embed:
        parent = flatten_schema(ws, spec.embed, seen)
        chain.extend(parent.chain)
        for k, v in parent.fields.items():
            fields.setdefault(k, v)
        closed = closed or parent.closed
    del seen[name]
    return FlatSchema(chain=chain, fields=fields, closed=closed)


def find_unknown_fields(flat: FlatSchema, cfg: ConfigSpec) -> list[str]:
    return [name for name in cfg.fields if name not in flat.fields]

def validate_closed(flat: FlatSchema, cfg: ConfigSpec) -> None:
    if not flat.closed:
        return
    unknown = find_unknown_fields(flat, cfg)
    if unknown:
        raise ValueError(f"closed schema rejects field {unknown[0]}")


def detect_embed_cycle(ws: Workspace) -> None:
    for name in ws.schemas:

        def walk(current: str, stack: set[str]) -> None:
            if current in stack:
                raise ValueError("embed cycle")
            stack.add(current)
            spec = ws.schemas[current]
            if spec.embed:
                walk(spec.embed, stack)
            stack.remove(current)

        walk(name, set())


def split_path(path: str) -> tuple[str, str]:
    parts = path.split(".")
    if len(parts) < 3:
        return "", ""
    return parts[1], parts[-1]


def build_lineage(cfg_id: str, schema_name: str, field: str, flat: FlatSchema) -> list[str]:
    return ["config." + cfg_id, *flat.chain, field]


def evaluate_workspace(ws: Workspace, seed: str) -> dict[str, Any]:
    detect_embed_cycle(ws)
    out: dict[str, Any] = {}
    for cfg_id, cfg in ws.configs.items():
        flat = flatten_schema(ws, cfg.schema)
        validate_closed(flat, cfg)
        for name, spec in flat.fields.items():
            path = f"config.{cfg_id}.{name}"
            val = cfg.fields.get(name)
            if val is None:
                if spec.optional:
                    continue
                raise ValueError(f"missing field {path}")
            if val.use_disjunct:
                if spec.typ != "disjunct":
                    raise ValueError(f"field {path} not disjunct")
                out[path] = resolve_disjunct_value(seed, spec.disjuncts)
                continue
            if spec.typ == "int":
                out[path] = int(val.literal)
            else:
                out[path] = val.literal
    return out


def build_vet_traces(ws: Workspace, seed: str, values: dict[str, Any]) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    for rule in ws.vet_rules:
        cfg_id, fld = split_path(rule.path)
        cfg = ws.configs[cfg_id]
        flat = flatten_schema(ws, cfg.schema)
        lineage = build_lineage(cfg_id, cfg.schema, fld, flat)
        detail = f"{rule.attr} check"
        if rule.attr == "default":
            spec = flat.fields.get(fld)
            if spec and spec.typ == "disjunct":
                detail = f"default disjunct [{' '.join(spec.disjuncts)}]"
        traces.append(
            {
                "path": rule.path,
                "attr": rule.attr,
                "lineage": lineage,
                "detail": detail,
            }
        )
    return traces


def reference_vet(directory: Path, seed: str) -> dict[str, Any]:
    ws = load_workspace(directory)
    try:
        values = evaluate_workspace(ws, seed)
    except ValueError as exc:
        return {
            "workspace": ws.name,
            "seed": seed,
            "ok": False,
            "error": str(exc),
            "traces": [],
        }
    try:
        detect_embed_cycle(ws)
    except ValueError as exc:
        return {
            "workspace": ws.name,
            "seed": seed,
            "ok": False,
            "error": str(exc),
            "traces": [],
        }
    for cfg in ws.configs.values():
        flat = flatten_schema(ws, cfg.schema)
        try:
            validate_closed(flat, cfg)
        except ValueError as exc:
            return {
                "workspace": ws.name,
                "seed": seed,
                "ok": False,
                "error": str(exc),
                "traces": build_vet_traces(ws, seed, values),
            }
    return {
        "workspace": ws.name,
        "seed": seed,
        "ok": True,
        "traces": build_vet_traces(ws, seed, values),
    }


def build_export_doc(ws: Workspace, seed: str, values: dict[str, Any]) -> dict[str, Any]:
    prov = [
        {
            "path": rule.path,
            "kind": "optional",
            "source": f"{rule.file}:{rule.line}",
        }
        for rule in ws.exports
        if rule.kind == "optional"
    ]
    return {
        "workspace": ws.name,
        "seed": seed,
        "values": values,
        "provenance": prov,
    }


def reference_export(directory: Path, seed: str) -> dict[str, Any]:
    ws = load_workspace(directory)
    values = evaluate_workspace(ws, seed)
    detect_embed_cycle(ws)
    for cfg in ws.configs.values():
        validate_closed(flatten_schema(ws, cfg.schema), cfg)
    return build_export_doc(ws, seed, values)


def trace_by_path(doc: dict[str, Any], path: str) -> dict[str, Any]:
    for row in doc.get("traces", []):
        if row["path"] == path:
            return row
    raise KeyError(path)


EVAL_SNAPSHOTS = Path("/app/state/eval-snapshots")


def eval_snapshot_path(ws_name: str, seed: str) -> Path:
    return EVAL_SNAPSHOTS / f"{ws_name}-{seed}.json"


def build_eval_snapshot(directory: Path, seed: str) -> dict[str, Any]:
    ws = load_workspace(directory)
    try:
        values = evaluate_workspace(ws, seed)
    except ValueError as exc:
        return {
            "version": 1,
            "workspace": ws.name,
            "seed": seed,
            "workspace_dir": str(directory),
            "ok": False,
            "error": str(exc),
        }
    try:
        detect_embed_cycle(ws)
    except ValueError as exc:
        return {
            "version": 1,
            "workspace": ws.name,
            "seed": seed,
            "workspace_dir": str(directory),
            "ok": False,
            "error": str(exc),
        }
    for cfg in ws.configs.values():
        try:
            validate_closed(flatten_schema(ws, cfg.schema), cfg)
        except ValueError as exc:
            return {
                "version": 1,
                "workspace": ws.name,
                "seed": seed,
                "workspace_dir": str(directory),
                "ok": False,
                "error": str(exc),
            }
    return {
        "version": 1,
        "workspace": ws.name,
        "seed": seed,
        "workspace_dir": str(directory),
        "ok": True,
        "values": values,
    }
