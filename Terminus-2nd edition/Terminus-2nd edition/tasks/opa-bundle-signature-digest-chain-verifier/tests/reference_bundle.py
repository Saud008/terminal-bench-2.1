"""Independent reference for bundlectl verify/eval contract acceptance."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path
from typing import Any

BUILD_SEED = "opa-bundle-signature-digest-chain-verifier"
KEYS_PATH = Path("/app/trust/keys.json")


def canonical(path: str) -> str:
    p = path.replace("\\", "/").removeprefix("./")
    parts: list[str] = []
    for part in p.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise ValueError(f"path escapes bundle root: {path}")
            parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def member_digest(content: bytes) -> bytes:
    return hashlib.sha256(content).digest()


def chain_root(members: list[tuple[str, bytes]]) -> tuple[str, dict[str, str]]:
    ordered = sorted(((canonical(p), b) for p, b in members), key=lambda x: x[0])
    digests: dict[str, str] = {}
    state = hashlib.sha256(b"").digest()
    for path, body in ordered:
        fd = member_digest(body)
        digests[path] = fd.hex()
        h = hashlib.sha256()
        h.update(state)
        h.update(path.encode())
        h.update(fd)
        state = h.digest()
    return state.hex(), digests


def scoped_root(members: list[tuple[str, bytes]], scope: str) -> str:
    subset = [(p, b) for p, b in members if canonical(p).startswith(scope)]
    root, _ = chain_root(subset)
    return root


def load_keys() -> dict[str, str]:
    return json.loads(KEYS_PATH.read_text(encoding="utf-8"))["keys"]


def load_bundle_members(bundle_dir: Path) -> list[tuple[str, bytes]]:
    manifest = json.loads((bundle_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    members: list[tuple[str, bytes]] = []
    for raw in manifest["members"]:
        if raw in ("MANIFEST.json", ".signatures.json"):
            continue
        can = canonical(raw)
        body = (bundle_dir / Path(*can.split("/"))).read_bytes()
        members.append((can, body))
    return members


def reference_verify(bundle_dir: Path) -> dict[str, Any]:
    try:
        members = load_bundle_members(bundle_dir)
    except ValueError as exc:
        return {"ok": False, "reason": str(exc)}
    except OSError as exc:
        return {"ok": False, "reason": str(exc)}

    sig = json.loads((bundle_dir / ".signatures.json").read_text(encoding="utf-8"))
    revoked_path = bundle_dir / "trust" / "revoked-keys.json"
    revoked_ids = {
        row["key_id"]
        for row in json.loads(revoked_path.read_text(encoding="utf-8")).get("revoked", [])
    }
    keys = load_keys()
    for ent in sig["signatures"]:
        if ent["key_id"] in revoked_ids:
            return {"ok": False, "revoked": True, "reason": "revoked key"}

    root, digests = chain_root(members)
    for ent in sig["signatures"]:
        expect = scoped_root(members, ent["scope"])
        if expect != ent["chain_root"]:
            return {"ok": False, "reason": f"scope {ent['scope']} chain mismatch"}
        mat = keys[ent["key_id"]]
        mac = hmac.new(mat.encode(), digestmod=hashlib.sha256)
        mac.update(ent["scope"].encode())
        mac.update(ent["chain_root"].encode())
        if mac.hexdigest() != ent["signature"]:
            return {"ok": False, "reason": f"bad signature for {ent['key_id']}"}
    return {"ok": True, "chain_root": root, "digests": digests}


def tag_numeric(seed: str) -> int:
    h = hashlib.sha256(f"{BUILD_SEED}:{seed}".encode()).digest()
    return ((h[0] << 8) | h[1]) % 900 + 100


def apply_threshold(content: bytes, seed: str) -> bytes:
    return content.replace(b"__THRESHOLD__", str(tag_numeric(seed)).encode())


_ALLOW = re.compile(r"allow\s*\{\s*(.+)\s*\}")


def parse_policy(source: str) -> tuple[str, str, str]:
    for line in source.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _ALLOW.search(line)
        if not m:
            continue
        expr = m.group(1).strip()
        for op in (">=", "<=", "!=", "==", ">", "<"):
            i = expr.find(op)
            if i > 0:
                return expr[:i].strip(), op, expr[i + len(op) :].strip()
    raise ValueError("allow rule not found")


def _lookup(ref: str, data: dict[str, Any], inp: dict[str, Any]) -> Any:
    if ref.startswith(("data.", "input.")):
        if ref.startswith("data."):
            return data[ref.removeprefix("data.")]
        return inp[ref.removeprefix("input.")]
    raise KeyError(ref)


def _to_float(v: Any) -> float:
    if isinstance(v, bool):
        raise TypeError("bool")
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        return float(v)
    raise TypeError(type(v))


def reference_eval(bundle_dir: Path, seed: str, input_path: Path) -> dict[str, Any]:
    policy = (bundle_dir / "policies" / "allow.rego").read_text(encoding="utf-8")
    left, op, right = parse_policy(policy)
    data = json.loads((bundle_dir / "data" / "data.json").read_text(encoding="utf-8"))
    raw_in = apply_threshold(input_path.read_bytes(), seed)
    inp = json.loads(raw_in)
    lv = _to_float(_lookup(left, data, inp) if left.startswith(("data.", "input.")) else left)
    rv = _to_float(_lookup(right, data, inp) if right.startswith(("data.", "input.")) else right)
    ops = {
        ">=": lv >= rv,
        ">": lv > rv,
        "<=": lv <= rv,
        "<": lv < rv,
        "==": lv == rv,
        "!=": lv != rv,
    }
    allow = ops[op]
    bindings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ref in (left, right):
        if ref.startswith(("data.", "input.")) and ref not in seen:
            seen.add(ref)
            bindings.append({"ref": ref, "value": _lookup(ref, data, inp)})
    return {
        "allow": allow,
        "trace": {
            "bindings": bindings,
            "steps": ["load_data", "eval_expr", "decision"],
        },
    }
