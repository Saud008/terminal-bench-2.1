"""Independent OpenAPI dereference and payload validator."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Discriminator:
    property_name: str
    mapping: dict[str, str]


@dataclass
class Schema:
    type: str = ""
    types: list[str] = field(default_factory=list)
    ref: str = ""
    properties: dict[str, Schema] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    all_of: list[Schema] = field(default_factory=list)
    default: Any = None
    additional_properties: bool | None = None
    discriminator: Discriminator | None = None


@dataclass
class Spec:
    paths: dict[str, dict[str, Any]]
    schemas: dict[str, Schema]


def order_payloads(seed: str, payloads: list[str]) -> list[str]:
    digest = hashlib.sha256(seed.encode()).digest()
    out = list(payloads)
    for i in range(len(out) - 1, 0, -1):
        j = digest[i % len(digest)] % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out


def select_payloads(seed: str, payloads: list[str]) -> list[str]:
    if not payloads:
        return []
    digest = hashlib.sha256(seed.encode()).digest()
    bits = digest[0] | (digest[1] << 8)
    limit = min(len(payloads), 16)
    selected = [payloads[i] for i in range(limit) if (bits >> i) & 1]
    if not selected:
        selected = [payloads[digest[2] % len(payloads)]]
    return order_payloads(seed, selected)


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def parse_schema(node: Any) -> Schema:
    if not isinstance(node, dict):
        return Schema()
    s = Schema()
    if "$ref" in node:
        s.ref = str(node["$ref"])
        return s
    if isinstance(node.get("type"), str):
        s.type = node["type"]
    if isinstance(node.get("type"), list):
        s.types = [str(t) for t in node["type"]]
    for k, v in (node.get("properties") or {}).items():
        s.properties[k] = parse_schema(v)
    s.required = [str(r) for r in node.get("required") or []]
    s.all_of = [parse_schema(item) for item in node.get("allOf") or []]
    if "default" in node:
        s.default = node["default"]
    if "additionalProperties" in node:
        s.additional_properties = bool(node["additionalProperties"])
    disc = node.get("discriminator")
    if isinstance(disc, dict):
        s.discriminator = Discriminator(
            property_name=str(disc.get("propertyName", "")),
            mapping={str(k): str(v) for k, v in (disc.get("mapping") or {}).items()},
        )
    return s


def load_spec(path: Path) -> Spec:
    root = yaml.safe_load(path.read_text(encoding="utf-8"))
    schemas: dict[str, Schema] = {}
    for name, node in (root.get("components", {}).get("schemas") or {}).items():
        schemas[name] = parse_schema(node)
    return Spec(paths=root.get("paths") or {}, schemas=schemas)


def operation_schema(spec: Spec, operation: str) -> Schema:
    method, path = operation.split(" ", 1)
    op = spec.paths[path][method.lower()]
    return parse_schema(op["requestBody"]["content"]["application/json"]["schema"])


def clone_schema(s: Schema) -> Schema:
    out = Schema(
        type=s.type,
        types=list(s.types),
        ref=s.ref,
        required=list(s.required),
        default=s.default,
        additional_properties=s.additional_properties,
    )
    out.properties = {k: clone_schema(v) for k, v in s.properties.items()}
    out.all_of = [clone_schema(part) for part in s.all_of]
    if s.discriminator:
        out.discriminator = Discriminator(s.discriminator.property_name, dict(s.discriminator.mapping))
    return out


def on_stack(stack: list[str], name: str) -> bool:
    return name in stack


def merge_schemas(parts: list[Schema]) -> Schema:
    out = Schema(type="object")
    seen: set[str] = set()
    for part in parts:
        for req in part.required:
            if req not in seen:
                out.required.append(req)
                seen.add(req)
        for k, v in part.properties.items():
            out.properties[k] = clone_schema(v)
        if part.discriminator:
            out.discriminator = part.discriminator
        if part.additional_properties is not None:
            out.additional_properties = part.additional_properties
    return out


def resolve(s: Schema | None, schemas: dict[str, Schema], stack: list[str]) -> tuple[Schema | None, int]:
    if s is None:
        return None, 0
    if s.ref:
        name = ref_name(s.ref)
        if on_stack(stack, name):
            return Schema(type="object"), 1
        target = schemas.get(name)
        if target is None:
            return None, 0
        return resolve(target, schemas, stack + [name])
    cycles = 0
    if s.all_of:
        parts: list[Schema] = []
        for part in s.all_of:
            resolved, c = resolve(part, schemas, stack)
            cycles += c
            if resolved is not None:
                parts.append(resolved)
        merged = merge_schemas(parts)
        if s.additional_properties is not None:
            merged.additional_properties = s.additional_properties
        for k, v in s.properties.items():
            resolved, c = resolve(v, schemas, stack)
            cycles += c
            if resolved is not None:
                merged.properties[k] = resolved
        return merged, cycles
    out = clone_schema(s)
    for k, v in out.properties.items():
        resolved, c = resolve(v, schemas, stack)
        cycles += c
        if resolved is not None:
            out.properties[k] = resolved
    return out, cycles


def apply_discriminator(base: Schema | None, data: dict[str, Any], schemas: dict[str, Schema]) -> tuple[Schema | None, int]:
    if base is None or base.discriminator is None:
        return base, 0
    raw = data.get(base.discriminator.property_name)
    if raw is None:
        return base, 0
    key = str(raw)
    ref = base.discriminator.mapping.get(key)
    if not ref:
        return base, 0
    sub = schemas.get(ref_name(ref))
    if sub is None:
        return base, 0
    resolved, cycles = resolve(sub, schemas, [])
    return merge_schemas([base, resolved]), cycles


def resolve_for_payload(s: Schema, schemas: dict[str, Schema], data: dict[str, Any]) -> tuple[Schema | None, int]:
    base, cycles = resolve(s, schemas, [])
    merged, extra = apply_discriminator(base, data, schemas)
    return merged, cycles + extra


def allows_null(s: Schema) -> bool:
    return "null" in s.types


def primary_type(s: Schema) -> str:
    if s.type:
        return s.type
    for t in s.types:
        if t != "null":
            return t
    return ""


def has_default(s: Schema | None, field: str) -> bool:
    if s is None:
        return False
    prop = s.properties.get(field)
    return prop is not None and prop.default is not None


def validate_data(data: dict[str, Any], schema: Schema | None) -> tuple[bool, list[str]]:
    if schema is None:
        return False, ["missing schema"]
    errors: list[str] = []
    for req in schema.required:
        if req not in data and not has_default(schema, req):
            errors.append(f"missing required {req}")
    for key, value in data.items():
        prop = schema.properties.get(key)
        if prop is None:
            if schema.additional_properties is False:
                errors.append(f"additional property {key}")
            continue
        if value is None:
            if not allows_null(prop):
                errors.append(f"{key} cannot be null")
            continue
        typ = primary_type(prop)
        if typ == "string" and not isinstance(value, str):
            errors.append(f"{key} must be string")
        elif typ == "integer" and not isinstance(value, (int, float)):
            errors.append(f"{key} must be integer")
        elif typ == "object" and not isinstance(value, dict):
            errors.append(f"{key} must be object")
    if schema.discriminator:
        raw = data.get(schema.discriminator.property_name)
        if raw is not None and str(raw) not in schema.discriminator.mapping:
            errors.append(f"unknown discriminator {raw}")
    return len(errors) == 0, errors


def reference_validate(config_path: Path, spec_path: Path, payload_dir: Path) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    seed = cfg["seed"]
    names = list(cfg["payloads"])
    selected = select_payloads(seed, names)
    spec = load_spec(spec_path)
    results = []
    stats = {"validated": 0, "valid": 0, "invalid": 0}
    for name in selected:
        env = json.loads((payload_dir / name).read_text(encoding="utf-8"))
        schema = operation_schema(spec, env["operation"])
        resolved, cycles = resolve_for_payload(schema, spec.schemas, env["data"])
        valid, errors = validate_data(env["data"], resolved)
        stats["validated"] += 1
        if valid:
            stats["valid"] += 1
        else:
            stats["invalid"] += 1
        results.append(
            {
                "file": name,
                "operation": env["operation"],
                "valid": valid,
                "errors": errors,
                "cycles_seen": cycles,
            }
        )
    return {"seed": seed, "payloads": selected, "results": results, "stats": stats}


def result_row(doc: dict, filename: str) -> dict:
    matches = [row for row in doc["results"] if row["file"] == filename]
    if len(matches) != 1:
        raise KeyError(f"expected one result for {filename}, got {len(matches)}")
    return matches[0]
