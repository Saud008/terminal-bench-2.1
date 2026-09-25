"""Independent Python reference for fc-alias-check golden semantics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ReferenceCycleError(Exception):
    """Raised when alias resolution detects a cycle."""


STAGE_PATH = Path("/app/state/fc-compiled.json")
COMPILE_SEQ_PATH = Path("/app/state/compile-seq.txt")
TB3_CONFIGS = Path("/opt/verifier-fixtures/fc-configs")


def parse_str(text: str) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "aliases": [],
        "charsets": [],
        "substitutes": [],
        "reject_bitmap": False,
        "reject_outline": False,
    }
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("<?")
        and not line.strip().startswith("<!")
    ]
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("<alias "):
            cfg["aliases"].append(
                (_attr(line, "from"), _attr(line, "to"))
            )
            i += 1
            continue
        if line.startswith("<charset "):
            name = _attr(line, "name")
            short = _attr(line, "short")
            encoding = _attr(line, "encoding")
            i += 1
            if i < len(lines) and "<alias ref=" in lines[i]:
                alias_ref = _attr(lines[i], "ref")
                i += 1
                if i < len(lines) and lines[i].startswith("</charset>"):
                    i += 1
            else:
                alias_ref = name
            cfg["charsets"].append(
                {
                    "name": name,
                    "short": short,
                    "encoding": encoding,
                    "alias_ref": alias_ref,
                }
            )
            continue
        if line.startswith("<substitute "):
            family = _attr(line, "family")
            i += 1
            preferred: list[str] = []
            while i < len(lines) and lines[i].startswith("<prefer>"):
                preferred.append(
                    lines[i]
                    .removeprefix("<prefer>")
                    .removesuffix("</prefer>")
                    .strip()
                )
                i += 1
            if i < len(lines) and lines[i].startswith("</substitute>"):
                i += 1
            cfg["substitutes"].append({"family": family, "preferred": preferred})
            continue
        if line.startswith("<reject-bitmap"):
            cfg["reject_bitmap"] = True
            i += 1
            continue
        if line.startswith("<reject-outline"):
            cfg["reject_outline"] = True
            i += 1
            continue
        if line in ("<fontconfig>", "</fontconfig>"):
            i += 1
            continue
        raise ValueError(f"unexpected line: {line}")
    return cfg


def _attr(line: str, key: str) -> str:
    needle = f'{key}="'
    start = line.index(needle) + len(needle)
    end = line.index('"', start)
    return line[start:end]


def parse_file(path: str | Path) -> dict[str, Any]:
    return parse_str(Path(path).read_text(encoding="utf-8"))


def merge_config(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    cfg = {
        "aliases": list(base["aliases"]),
        "charsets": list(base["charsets"]),
        "substitutes": list(base["substitutes"]),
        "reject_bitmap": base["reject_bitmap"],
        "reject_outline": base["reject_outline"],
    }
    for from_name, to_name in overlay["aliases"]:
        for idx, (existing_from, _) in enumerate(cfg["aliases"]):
            if existing_from == from_name:
                cfg["aliases"][idx] = (from_name, to_name)
                break
        else:
            cfg["aliases"].append((from_name, to_name))
    for cs in overlay["charsets"]:
        for idx, existing in enumerate(cfg["charsets"]):
            if existing["name"] == cs["name"]:
                cfg["charsets"][idx] = cs
                break
        else:
            cfg["charsets"].append(cs)
    for sub in overlay["substitutes"]:
        for idx, existing in enumerate(cfg["substitutes"]):
            if existing["family"] == sub["family"]:
                cfg["substitutes"][idx] = sub
                break
        else:
            cfg["substitutes"].append(sub)
    if overlay["reject_bitmap"]:
        cfg["reject_bitmap"] = True
    if overlay["reject_outline"]:
        cfg["reject_outline"] = True
    return cfg


def load_merged(base: Path, inject: Path | None = None) -> dict[str, Any]:
    cfg = parse_file(base)
    if inject is not None:
        cfg = merge_config(cfg, parse_file(inject))
    return cfg


def find_cycle(cfg: dict[str, Any]) -> None:
    edges = {a: b for a, b in cfg["aliases"]}
    for start, _ in cfg["aliases"]:
        seen: set[str] = set()
        current = start
        while True:
            if current in seen:
                raise ReferenceCycleError("alias cycle detected")
            seen.add(current)
            nxt = edges.get(current)
            if nxt is None:
                break
            current = nxt


def lookup_charset(cfg: dict[str, Any], name: str) -> dict[str, Any]:
    for cs in cfg["charsets"]:
        if cs["name"] == name:
            return cs
    raise KeyError(f"unknown charset {name}")


def expand_alias_chain(cfg: dict[str, Any], start: str) -> tuple[list[str], str]:
    edges = {a: b for a, b in cfg["aliases"]}
    chain: list[str] = []
    seen: set[str] = set()
    current = start
    while True:
        if current in seen:
            raise ReferenceCycleError("alias cycle detected")
        seen.add(current)
        try:
            lookup_charset(cfg, current)
            return chain, current
        except KeyError:
            pass
        nxt = edges.get(current)
        if nxt is None:
            raise KeyError(f"unknown alias {current}")
        chain.append(current)
        current = nxt


def compute_font_kinds(reject_bitmap: bool, reject_outline: bool) -> list[str]:
    kinds: list[str] = []
    if not reject_bitmap:
        kinds.append("bitmap")
    if not reject_outline:
        kinds.append("outline")
    return kinds


def read_compile_seq() -> int:
    if not COMPILE_SEQ_PATH.is_file():
        return 0
    return int(COMPILE_SEQ_PATH.read_text(encoding="utf-8").strip() or "0")


def graph_hash(cfg: dict[str, Any], base: Path, inject: Path | None) -> str:
    inject_key = str(inject) if inject is not None else ""
    canonical = json.dumps(cfg, separators=(",", ":"))
    payload = f"{base}\n{inject_key}\n{canonical}"
    h = 5381
    for b in payload.encode("utf-8"):
        h = ((h * 33) + b) & 0xFFFFFFFFFFFFFFFF
    return f"{h:016x}"


def compile_meta_for(
    cfg: dict[str, Any], base: Path, inject: Path | None, seq: int | None = None
) -> dict[str, Any]:
    if seq is None:
        seq = read_compile_seq() or 1
    return {
        "compile_seq": seq,
        "graph_hash": graph_hash(cfg, base, inject),
    }


def resolve_request(
    cfg: dict[str, Any],
    charset_query: str,
    family_query: str,
    compile_meta: dict[str, Any],
) -> dict[str, Any]:
    charset = lookup_charset(cfg, charset_query)
    alias_chain, terminal = expand_alias_chain(cfg, charset["alias_ref"])
    terminal_entry = lookup_charset(cfg, terminal)
    encoding = terminal_entry["encoding"]

    substitute = next(
        (s for s in cfg["substitutes"] if s["family"] == family_query),
        {"family": family_query, "preferred": []},
    )

    return {
        "schema": "fc-alias-check/1",
        "charset_query": charset_query,
        "family_query": family_query,
        "charset": {
            "name": charset["name"],
            "short": charset["short"],
            "encoding": charset["encoding"],
            "alias_ref": charset["alias_ref"],
        },
        "alias_chain": alias_chain,
        "resolved_terminal": terminal,
        "encoding": encoding,
        "substitute": {
            "family": substitute["family"],
            "preferred": list(substitute["preferred"]),
        },
        "reject_bitmap": cfg["reject_bitmap"],
        "reject_outline": cfg["reject_outline"],
        "font_kinds_allowed": compute_font_kinds(
            cfg["reject_bitmap"], cfg["reject_outline"]
        ),
        "compile_meta": compile_meta,
    }


def resolve_documents(
    config: Path,
    charset: str,
    family: str,
    inject: Path | None = None,
    compile_seq: int | None = None,
) -> dict[str, Any]:
    cfg = load_merged(config, inject)
    find_cycle(cfg)
    meta = compile_meta_for(cfg, config, inject, compile_seq)
    return resolve_request(cfg, charset, family, meta)


def expected_stage(config: Path, inject: Path | None = None) -> dict[str, Any]:
    cfg = load_merged(config, inject)
    seq = read_compile_seq() or 1
    return {
        "schema": "fc-compiled/1",
        "compile_meta": compile_meta_for(cfg, config, inject, seq),
        "config_path": str(config),
        "inject_path": str(inject) if inject is not None else None,
        "config": cfg,
    }
