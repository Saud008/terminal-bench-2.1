"""Independent syslog-ng replay evaluator for behavioral verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Route:
    route_id: str
    filter_id: str
    destination: str
    fallback: bool
    dead: bool


@dataclass(frozen=True)
class Rewrite:
    rewrite_id: str
    filter_ref: str
    template: str


@dataclass(frozen=True)
class Message:
    msg_id: str
    facility: str
    level: str
    program: str
    host: str
    text: str

    def as_line(self) -> str:
        return f"{self.msg_id},{self.facility},{self.level},{self.program},{self.host},{self.text}"


def load_filters(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        fid, expr = line.split("|", 1)
        out[fid] = expr.replace(" ", "")
    return out


def load_routes(path: Path) -> List[Route]:
    routes: List[Route] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        rid, fid, dest, fallback, dead = line.split("|")
        routes.append(Route(rid, fid, dest, fallback == "1", dead == "1"))
    return routes


def load_rewrites(path: Path) -> List[Rewrite]:
    items: List[Rewrite] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        rw_id, ref, template = line.split("|")
        items.append(Rewrite(rw_id, ref, template))
    return items


def load_messages(path: Path) -> List[Message]:
    msgs: List[Message] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        mid, fac, lvl, prog, host, text = line.split(",", 5)
        msgs.append(Message(mid, fac, lvl, prog, host, text))
    return msgs


def config_hash(config_dir: Path) -> str:
    parts = []
    for name in ("filters.conf", "graph.conf", "rewrites.conf"):
        parts.append((config_dir / name).read_text(encoding="utf-8"))
    digest = hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
    return digest


def prune_routes(
    routes: List[Route], filters: Dict[str, str], rewrites: List[Rewrite]
) -> List[Route]:
    rewrite_refs = {rw.filter_ref for rw in rewrites}
    active: List[Route] = []
    for route in routes:
        if route.filter_id not in filters:
            continue
        if route.dead and not route.fallback and route.filter_id not in rewrite_refs:
            continue
        active.append(route)
    return active


def _match_atom(atom: str, msg: Message) -> bool:
    if atom.startswith("facility(") and atom.endswith(")"):
        return msg.facility == atom[len("facility(") : -1]
    if atom.startswith("level(") and atom.endswith(")"):
        return msg.level == atom[len("level(") : -1]
    if atom.startswith("program(") and atom.endswith(")"):
        return msg.program == atom[len("program(") : -1]
    return False


def _parse_expr(expr: str) -> Tuple[str, str | None, str | None]:
    expr = expr.replace(" ", "")
    depth = 0
    for idx, ch in enumerate(expr):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and ch == "|" and idx + 1 < len(expr) and expr[idx + 1] == "|":
            return "or", expr[:idx], expr[idx + 2 :]
    depth = 0
    for idx, ch in enumerate(expr):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and ch == "&" and idx + 1 < len(expr) and expr[idx + 1] == "&":
            return "and", expr[:idx], expr[idx + 2 :]
    if expr.startswith("(") and expr.endswith(")"):
        return "paren", expr[1:-1], None
    return "atom", expr, None


def eval_expr(expr: str, msg: Message) -> bool:
    kind, left, right = _parse_expr(expr)
    if kind == "atom":
        return _match_atom(left, msg)
    if kind == "paren":
        return eval_expr(left, msg)
    if kind == "and":
        return eval_expr(left, msg) and eval_expr(right or "", msg)
    if kind == "or":
        return eval_expr(left, msg) or eval_expr(right or "", msg)
    return False


def pure_facility_gates(filters: Dict[str, str]) -> List[str]:
    gates: List[str] = []
    for _fid, expr in filters.items():
        cleaned = expr.replace(" ", "")
        if cleaned.startswith("facility(") and cleaned.endswith(")") and "&&" not in cleaned and "||" not in cleaned:
            gates.append(cleaned[len("facility(") : -1])
    return gates


def passes_facility_gate(msg: Message, filters: Dict[str, str]) -> bool:
    gates = pure_facility_gates(filters)
    if not gates:
        return True
    return msg.facility in gates


def apply_rewrites(msg: Message, rewrites: List[Rewrite], filters: Dict[str, str]) -> Tuple[Message, bool]:
    program = msg.program
    applied = False
    for rw in rewrites:
        expr = filters.get(rw.filter_ref, "")
        if expr and eval_expr(expr, msg):
            program = f"{rw.template}{program}"
            applied = True
    return Message(msg.msg_id, msg.facility, msg.level, program, msg.host, msg.text), applied


def evaluate(
    config_dir: Path, messages_path: Path, seed: str, reload_mode: str = "full"
) -> Tuple[dict, dict]:
    filters = load_filters(config_dir / "filters.conf")
    routes = load_routes(config_dir / "graph.conf")
    rewrites = load_rewrites(config_dir / "rewrites.conf")
    messages = load_messages(messages_path)

    active = prune_routes(routes, filters, rewrites)
    cfg_hash = config_hash(config_dir)

    deliveries: Dict[str, int] = {}
    dropped = 0
    rewrite_count = 0

    for msg in messages:
        if not passes_facility_gate(msg, filters):
            dropped += 1
            continue
        msg2, applied = apply_rewrites(msg, rewrites, filters)
        if applied:
            rewrite_count += 1
        for route in active:
            expr = filters[route.filter_id]
            if eval_expr(expr, msg2):
                deliveries[route.destination] = deliveries.get(route.destination, 0) + 1

    total_deliveries = sum(deliveries.values())
    report = {
        "seed": seed,
        "config_dir": str(config_dir),
        "messages_path": str(messages_path),
        "total_messages": len(messages),
        "dropped_at_facility_gate": dropped,
        "total_deliveries": total_deliveries,
        "rewrite_applied": rewrite_count,
        "deliveries": [
            {"destination": dest, "count": deliveries[dest]}
            for dest in sorted(deliveries)
        ],
    }
    snapshot = {
        "seed": seed,
        "config_dir": str(config_dir),
        "messages_path": str(messages_path),
        "processed_messages": len(messages),
        "dropped_at_facility_gate": dropped,
        "rewrite_applied": rewrite_count,
        "config_hash": cfg_hash,
        "active_routes": [r.route_id for r in active],
    }
    return report, snapshot
