"""Independent reference for xanesctl close digests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class XanesRefError(Exception):
    pass


EDGE_ORD = {
    "K": 1,
    "L1": 2,
    "L2": 3,
    "L3": 4,
    "M1": 5,
    "M2": 6,
    "M3": 7,
    "M4": 8,
    "M5": 9,
}


def fnv1a64(text: str) -> int:
    h = 0xCBF29CE484222325
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def edge_ordinal(code: str) -> int:
    if code not in EDGE_ORD:
        raise XanesRefError(f"unknown edge_code: {code}")
    return EDGE_ORD[code]


def fit_victoreen(energies: list[float], mus: list[float]) -> tuple[float, float]:
    n = len(energies)
    if n == 0:
        return 0.0, 0.0
    if n == 1:
        return mus[0], 0.0
    xs = [e ** (-3) for e in energies]
    sum_x = sum(xs)
    sum_y = sum(mus)
    sum_xx = sum(x * x for x in xs)
    sum_xy = sum(x * y for x, y in zip(xs, mus))
    nf = float(n)
    denom = nf * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-18:
        return sum_y / nf, 0.0
    b = (nf * sum_xy - sum_x * sum_y) / denom
    a = (sum_y - b * sum_x) / nf
    return a, b


def evaluate(a: float, b: float, e: float) -> float:
    return a + b * (e ** (-3))


def trapezoid(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    acc = 0.0
    for i in range(len(xs) - 1):
        acc += 0.5 * (ys[i] + ys[i + 1]) * (xs[i + 1] - xs[i])
    return acc


def round6(v: float) -> float:
    return round(v * 1_000_000.0) / 1_000_000.0


def apply_seed(points: list[tuple[float, float]], seed: str, top_windows: list[dict]) -> list[tuple[float, float]]:
    target = (fnv1a64(seed) % 5) + 1
    bin_idx = 0
    hit = None
    pts = list(points)
    for i, (e, _) in enumerate(pts):
        inside = any(w["e_lo"] <= e <= w["e_hi"] for w in top_windows)
        if inside:
            bin_idx += 1
            if bin_idx == target:
                hit = i
                break
    if hit is not None:
        e, mu = pts[hit]
        pts[hit] = (e + 0.15, mu)
        pts.sort(key=lambda p: p[0])
    return pts


def check_undeclared(node: dict, ancestors: list[str]) -> None:
    code = node["edge_code"]
    if code.startswith("?"):
        raise XanesRefError(f"undeclared edge_code: {code}")
    edge_ordinal(code)
    scope = ancestors + [code]
    for child in node.get("children") or []:
        check_undeclared(child, scope)


def sort_channels(refs: list[dict[str, Any]]) -> list[str]:
    keyed = []
    for r in refs:
        keyed.append((r["atomic_number"], edge_ordinal(r["edge_code"]), r["channel_id"]))
    keyed.sort()
    return [k[2] for k in keyed]


def walk(node: dict, points: list[tuple[float, float]], a: float, b: float, outs: list[dict]) -> None:
    edge_ordinal(node["edge_code"])
    xs: list[float] = []
    ys: list[float] = []
    for e, mu in points:
        if node["e_lo"] <= e <= node["e_hi"]:
            xs.append(e)
            ys.append(mu - evaluate(a, b, e))
    integral = round6(trapezoid(xs, ys))
    ch_refs = [
        {
            "channel_id": cid,
            "atomic_number": node["atomic_number"],
            "edge_code": node["edge_code"],
        }
        for cid in node.get("channels") or []
    ]
    outs.append(
        {
            "window_id": node["window_id"],
            "element": node["element"],
            "edge_code": node["edge_code"],
            "integral": integral,
            "channels_sorted": sort_channels(ch_refs),
        }
    )
    for child in node.get("children") or []:
        walk(child, points, a, b, outs)


def collect_channels(node: dict, acc: list[dict]) -> None:
    for cid in node.get("channels") or []:
        acc.append(
            {
                "channel_id": cid,
                "atomic_number": node["atomic_number"],
                "edge_code": node["edge_code"],
            }
        )
    for child in node.get("children") or []:
        collect_channels(child, acc)


def closure_digest(outs: list[dict]) -> str:
    rows = [{"window_id": w["window_id"], "integral": w["integral"]} for w in outs]
    rows.sort(key=lambda r: r["window_id"])
    compact = json.dumps(rows, separators=(",", ":"))
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


def reference_close(trace_path: Path, windows_path: Path, seed: str = "") -> dict[str, Any]:
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    winfile = json.loads(windows_path.read_text(encoding="utf-8"))
    for w in winfile["windows"]:
        check_undeclared(w, [])

    points = [(p["e_ev"], p["mu"]) for p in trace["points"]]
    points.sort(key=lambda p: p[0])
    if seed:
        points = apply_seed(points, seed, winfile["windows"])

    min_lo = min(w["e_lo"] for w in winfile["windows"])
    pre = [(e, mu) for e, mu in points if e < min_lo]
    a, b = fit_victoreen([p[0] for p in pre], [p[1] for p in pre])

    outs: list[dict] = []
    for w in winfile["windows"]:
        walk(w, points, a, b, outs)

    all_refs: list[dict] = []
    for w in winfile["windows"]:
        collect_channels(w, all_refs)

    return {
        "status": "ok",
        "trace_id": trace["trace_id"],
        "windows": outs,
        "all_channels_sorted": sort_channels(all_refs),
        "closure_digest": closure_digest(outs),
    }
