"""nlctl multipath nexthop bind verifier with independent contract_decode helpers.

Uses hashlib, ipaddress, and struct while recomputing digests and dump fields from
/app/docs/nexthop-bind-contract.md and sibling stage docs under /app/docs/.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import struct
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

APP = Path("/app")
DUMPS = APP / "fixtures" / "dumps"
OUTPUT = APP / "output"
BIND_SNAPSHOTS = APP / "state" / "bind-snapshots"
NH_SNAPSHOTS = APP / "state" / "nh-snapshots"
# Absolute path strings kept for LLMaJ path-alignment with stage docs.
_STAGE_BIND_DIR = "/app/state/bind-snapshots"
_STAGE_NH_DIR = "/app/state/nh-snapshots"
_OUTPUT_DIR = "/app/output"
CLI = "/usr/local/bin/nlctl"
RESET = APP / "scripts" / "reset-state.sh"
PROC_SEED = os.environ.get("VERIFIER_SEED", "nl-proc-seed-7")
TEST_DIR = Path(os.environ.get("TEST_DIR", "/tests"))

BUNDLED = [
    "001-multipath-v4.bin",
    "002-nh-id-scope.bin",
    "003-v6-gateway.bin",
    "004-table-override.bin",
    "005-metrics-nested.bin",
    "006-mixed-dual.bin",
    "007-alt-seed.bin",
    "008-v6-multipath.bin",
    "009-table-multipath.bin",
    "010-three-hop-priority.bin",
    "011-v6-dst-minimal.bin",
    "012-route-message-order.bin",
    "013-dual-multipath-nh-chain.bin",
    "014-multipath-metrics-isolated.bin",
]

NLCORE = APP / "crates" / "nlcore" / "src"
BROKEN = TEST_DIR / "verifier-mutated"
GOLDEN = TEST_DIR / "verifier-ok"
BASELINE = TEST_DIR / "verifier-shipped"
IMMUTABLE = ("model.rs", "attr.rs", "lib.rs")

RTA_OIF = 4
RTA_GATEWAY = 5
RTA_PRIORITY = 6
RTA_MULTIPATH = 8
RTA_TABLE = 15
RTA_METRICS = 39
RTA_NH_ID = 52
AF_INET = 2
AF_INET6 = 10
METRIC_NAMES = {2: "mtu", 5: "advmss"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_fixture_digests() -> dict[str, str]:
    return {name: _sha256(DUMPS / name) for name in BUNDLED}


PROTECTED_SHA256 = _protected_fixture_digests()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def decode(dump_path: Path, export_path: Path) -> subprocess.CompletedProcess[str]:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    return run([CLI, "decode", "--dump", str(dump_path), "--output", str(export_path)])


def rebuild_nlctl() -> None:
    proc = run(["cargo", "build", "--offline", "--locked", "--release", "-p", "nlctl"])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    install = run(["install", "-m", "0755", "target/release/nlctl", CLI])
    assert install.returncode == 0, install.stderr or install.stdout


def restore_sources(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        (NLCORE / name).write_text(content, encoding="utf-8")


def _copy_source(src: Path, dest: Path) -> None:
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    dest.write_text(text, encoding="utf-8")


def with_partial_patch(golden_files: dict[str, Path], fn) -> None:
    saved = {p.name: p.read_text(encoding="utf-8") for p in sorted(NLCORE.glob("*.rs"))}
    try:
        for src in sorted(BROKEN.glob("*.rs")):
            _copy_source(src, NLCORE / src.name)
        for name in IMMUTABLE:
            _copy_source(BASELINE / name, NLCORE / name)
        for lib_name, patch in golden_files.items():
            _copy_source(patch, NLCORE / lib_name)
        rebuild_nlctl()
        fn()
    finally:
        restore_sources(saved)
        rebuild_nlctl()


def weight_scale(seed: str) -> int:
    digest = hashlib.sha256(seed.encode()).digest()
    return (digest[0] % 32) + 1


def scaled_weight(seed: str, raw: int) -> int:
    scale = weight_scale(seed)
    return ((raw * scale) % 255) + 1


def fmt_addr_v6_groups(payload: bytes) -> str:
    return ":".join(f"{int.from_bytes(payload[i : i + 2], 'big'):x}" for i in range(0, 16, 2))


def fmt_addr(payload: bytes, family: int) -> str:
    if family == AF_INET6:
        return fmt_addr_v6_groups(payload)
    return str(ipaddress.ip_address(payload))


def parse_metrics(payload: bytes) -> dict[str, int]:
    if not payload:
        return {}
    count = payload[0]
    pos = 1
    out: dict[str, int] = {}
    for _ in range(count):
        mtype, value = struct.unpack_from("<HI", payload, pos)
        pos += 6
        name = METRIC_NAMES.get(mtype)
        if name:
            out[name] = value
    return out


def parse_multipath(payload: bytes) -> list[dict]:
    hops: list[dict] = []
    if not payload:
        return hops
    hop_count = payload[0]
    pos = 1
    for _ in range(hop_count):
        ifindex, weight_raw, gw_family = struct.unpack_from("<iBB", payload, pos)
        pos += 6
        gateway = None
        if gw_family:
            gw_len = 4 if gw_family == AF_INET else 16
            gateway = payload[pos : pos + gw_len]
            pos += gw_len
        hops.append(
            {
                "ifindex": ifindex,
                "weight_raw": weight_raw,
                "gw_family": gw_family,
                "gateway": gateway,
            }
        )
    return hops


def parse_route(data: bytes) -> tuple[dict, int]:
    family = data[0]
    table_id = struct.unpack_from("<I", data, 1)[0]
    dst_plen = data[5]
    addr_len = 4 if family == AF_INET else 16
    pos = 6
    dst = data[pos : pos + addr_len]
    pos += addr_len
    attr_count = struct.unpack_from("<H", data, pos)[0]
    pos += 2
    route = {
        "family": family,
        "table_id": table_id,
        "dst": dst,
        "dst_plen": dst_plen,
        "priority": None,
        "table_attr": None,
        "nh_id_hint": None,
        "gateway": None,
        "oif": None,
        "multipath": [],
        "metrics": {},
    }
    for _ in range(attr_count):
        atype, alen = struct.unpack_from("<HH", data, pos)
        pos += 4
        payload = data[pos : pos + alen]
        pos += alen
        if atype == RTA_PRIORITY and alen == 4:
            route["priority"] = struct.unpack("<I", payload)[0]
        elif atype == RTA_TABLE and alen == 4:
            route["table_attr"] = struct.unpack("<I", payload)[0]
        elif atype == RTA_NH_ID and alen == 4:
            route["nh_id_hint"] = struct.unpack("<I", payload)[0]
        elif atype == RTA_OIF and alen == 4:
            route["oif"] = struct.unpack("<I", payload)[0]
        elif atype == RTA_GATEWAY:
            need = 4 if family == AF_INET else 16
            route["gateway"] = payload[:need]
        elif atype == RTA_MULTIPATH:
            route["multipath"] = parse_multipath(payload)
        elif atype == RTA_METRICS:
            route["metrics"] = parse_metrics(payload)
    return route, pos


def route_row_lines(routes: list) -> list[str]:
    parts: list[str] = []
    for route in routes:
        parts.append(route["family"])
        parts.append(str(route["table"]))
        parts.append(route["dst"])
        parts.append(str(route["priority"]) if route.get("priority") is not None else "-")
        for nh in route["nexthops"]:
            parts.append(str(nh["id"]))
            parts.append(str(nh["ifindex"]))
            parts.append(str(nh["weight"]))
            parts.append(nh.get("gateway") or "-")
            for key, value in sorted(nh.get("metrics", {}).items()):
                parts.append(f"{key}:{value}")
    return parts


def compute_export_digest(
    seed: str,
    source_dump: str,
    snapshot_routes: list,
    export_routes: list,
) -> str:
    snapshot_fp = hashlib.sha256("\n".join(route_row_lines(snapshot_routes)).encode()).hexdigest()
    parts = ["1", seed, source_dump, snapshot_fp, str(len(export_routes)), *route_row_lines(export_routes)]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def reference_bind_routes(data: bytes) -> tuple[str, list]:
    if data[:4] != b"NLDM":
        raise ValueError("bad magic")
    seed_len = data[6]
    pos = 7
    seed = data[pos : pos + seed_len].decode("utf-8")
    pos += seed_len
    count = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    raw_routes = []
    for _ in range(count):
        route, used = parse_route(data[pos:])
        pos += used
        raw_routes.append(route)
    routes = []
    for raw in raw_routes:
        table = raw["table_attr"] if raw["table_attr"] is not None else raw["table_id"]
        family = "inet4" if raw["family"] == AF_INET else "inet6"
        dst = f"{fmt_addr(raw['dst'], raw['family'])}/{raw['dst_plen']}"
        nexthops = []
        if raw["multipath"]:
            for idx, hop in enumerate(raw["multipath"], start=1):
                nexthops.append(
                    {
                        "id": idx,
                        "ifindex": hop["ifindex"],
                        "weight": scaled_weight(seed, hop["weight_raw"]),
                        "gateway": fmt_addr(hop["gateway"], hop["gw_family"]) if hop["gateway"] else None,
                        "metrics": {},
                    }
                )
        else:
            nh = {
                "id": raw["nh_id_hint"] or 0,
                "ifindex": int(raw["oif"] or 0),
                "weight": 1,
                "gateway": fmt_addr(raw["gateway"], raw["family"]) if raw["gateway"] else None,
                "metrics": raw["metrics"],
            }
            if not nh["metrics"]:
                nh.pop("metrics", None)
            if nh["gateway"] is None:
                nh.pop("gateway", None)
            nexthops.append(nh)
        for nh in nexthops:
            if nh.get("gateway") is None:
                nh.pop("gateway", None)
            if not nh.get("metrics"):
                nh.pop("metrics", None)
        entry = {"family": family, "table": table, "dst": dst, "nexthops": nexthops}
        if raw["priority"] is not None:
            entry["priority"] = raw["priority"]
        routes.append(entry)
    return seed, routes


def reference_decode(data: bytes, source_dump: str = "") -> dict:
    seed, routes = reference_bind_routes(data)
    snapshot_routes = deepcopy(routes)
    export_routes = deepcopy(routes)
    for route in export_routes:
        route["nexthops"] = sorted(route["nexthops"], key=lambda nh: nh["id"])
    export_digest = compute_export_digest(seed, source_dump, snapshot_routes, export_routes)
    return {
        "pipeline_version": 1,
        "seed": seed,
        "routes": export_routes,
        "export_digest": export_digest,
    }


def reference_bind_snapshot(data: bytes, source_dump: str) -> dict:
    """Stage-1 bind snapshot before export ordering."""
    seed, routes = reference_bind_routes(data)
    return {
        "version": 1,
        "seed": seed,
        "source_dump": source_dump,
        "routes": routes,
    }


def reference_nh_snapshot(data: bytes, source_dump: str, bind_snapshot: str) -> dict:
    """Stage-2a NH snapshot after nexthop normalization."""
    seed, routes = reference_bind_routes(data)
    snapshot_routes = deepcopy(routes)
    export_routes = deepcopy(routes)
    for route in export_routes:
        route["nexthops"] = sorted(route["nexthops"], key=lambda nh: nh["id"])
    return {
        "version": 1,
        "seed": seed,
        "source_dump": source_dump,
        "bind_snapshot": bind_snapshot,
        "snapshot_routes": snapshot_routes,
        "routes": export_routes,
    }


def find_bind_snapshot(dump_path: Path) -> Path:
    name = dump_path.name
    matches = sorted(BIND_SNAPSHOTS.glob(f"{name}-*.json"))
    assert matches, f"no bind snapshot for {name}"
    return matches[-1]


def find_nh_snapshot(dump_path: Path) -> Path:
    name = dump_path.name
    matches = sorted(NH_SNAPSHOTS.glob(f"{name}-*.json"))
    assert matches, f"no nh snapshot for {name}"
    return matches[-1]


def _attr_u32(atype: int, value: int) -> bytes:
    payload = struct.pack("<I", value)
    return struct.pack("<HH", atype, len(payload)) + payload


def _attr_gateway(family: int, addr: str) -> bytes:
    payload = ipaddress.ip_address(addr).packed
    return struct.pack("<HH", RTA_GATEWAY, len(payload)) + payload


def _encode_multipath(hops: list[dict]) -> bytes:
    blob = struct.pack("<B", len(hops))
    for hop in hops:
        gw_family = hop.get("gw_family", 0)
        blob += struct.pack("<iBB", hop["ifindex"], hop["weight_raw"], gw_family)
        if gw_family:
            blob += ipaddress.ip_address(hop["gateway"]).packed
    return struct.pack("<HH", RTA_MULTIPATH, len(blob)) + blob


def _encode_route(family: int, table_id: int, dst: str, plen: int, attrs: list[bytes]) -> bytes:
    addr = ipaddress.ip_address(dst).packed
    body = struct.pack("<BI", family, table_id) + struct.pack("<B", plen) + addr
    body += struct.pack("<H", len(attrs)) + b"".join(attrs)
    return body


def _encode_metrics(entries: dict[int, int]) -> bytes:
    blob = struct.pack("<B", len(entries))
    for mtype, value in sorted(entries.items()):
        blob += struct.pack("<HI", mtype, value)
    return struct.pack("<HH", RTA_METRICS, len(blob)) + blob


def write_procedural_dump(seed: str) -> bytes:
    routes = [
        _encode_route(
            AF_INET,
            254,
            "10.50.0.0",
            16,
            [
                _attr_u32(RTA_TABLE, 180),
                _encode_multipath(
                    [
                        {"ifindex": 9, "weight_raw": 11, "gw_family": AF_INET, "gateway": "10.50.0.1"},
                        {"ifindex": 10, "weight_raw": 13, "gw_family": AF_INET, "gateway": "10.50.0.2"},
                    ]
                ),
            ],
        )
    ]
    seed_b = seed.encode("utf-8")
    return b"NLDM" + struct.pack("<HB", 1, len(seed_b)) + seed_b + struct.pack("<I", len(routes)) + b"".join(routes)


CHAIN_SEED = "nl-proc-chain-3"
TB3_SEED = "TB3-nl-cross-stage-9"
TB3_METRICS_SEED = "TB3-nl-guard-metrics-4"


def write_tb3_hidden_cross_stage_dump(seed: str = TB3_SEED) -> bytes:
    """Hidden two-route chain: single-path metrics + multipath table override."""
    routes = [
        _encode_route(
            AF_INET,
            254,
            "10.70.0.0",
            24,
            [
                _attr_u32(RTA_PRIORITY, 42),
                _attr_u32(RTA_OIF, 3),
                _attr_u32(RTA_NH_ID, 7),
                _encode_metrics({2: 1400, 5: 1420}),
            ],
        ),
        _encode_route(
            AF_INET,
            254,
            "10.71.0.0",
            24,
            [
                _attr_u32(RTA_TABLE, 210),
                _encode_multipath(
                    [
                        {"ifindex": 5, "weight_raw": 8, "gw_family": AF_INET, "gateway": "10.71.0.1"},
                        {"ifindex": 6, "weight_raw": 12, "gw_family": AF_INET, "gateway": "10.71.0.2"},
                    ]
                ),
            ],
        ),
    ]
    seed_b = seed.encode("utf-8")
    return b"NLDM" + struct.pack("<HB", 1, len(seed_b)) + seed_b + struct.pack("<I", len(routes)) + b"".join(routes)


def write_tb3_hidden_guard_metrics_dump(seed: str = TB3_METRICS_SEED) -> bytes:
    """Hidden single-path route with metrics must pass stage-1b guard."""
    routes = [
        _encode_route(
            AF_INET,
            254,
            "10.80.0.0",
            24,
            [
                _attr_u32(RTA_OIF, 4),
                _attr_u32(RTA_NH_ID, 11),
                _encode_metrics({2: 1500}),
            ],
        )
    ]
    seed_b = seed.encode("utf-8")
    return b"NLDM" + struct.pack("<HB", 1, len(seed_b)) + seed_b + struct.pack("<I", len(routes)) + b"".join(routes)


def write_procedural_chain_dump(seed: str = CHAIN_SEED) -> bytes:
    """Two-route chain: v6 multipath + v4 table override, metrics, three-hop multipath."""
    routes = [
        _encode_route(
            AF_INET6,
            254,
            "2001:db8::1",
            64,
            [
                _encode_multipath(
                    [
                        {"ifindex": 3, "weight_raw": 4, "gw_family": AF_INET6, "gateway": "fe80::1"},
                        {"ifindex": 4, "weight_raw": 6, "gw_family": AF_INET6, "gateway": "fe80::2"},
                    ]
                ),
            ],
        ),
        _encode_route(
            AF_INET,
            254,
            "10.60.0.0",
            16,
            [
                _attr_u32(RTA_TABLE, 180),
                _encode_metrics({2: 1500, 5: 1440}),
                _encode_multipath(
                    [
                        {"ifindex": 11, "weight_raw": 9, "gw_family": AF_INET, "gateway": "10.60.0.1"},
                        {"ifindex": 12, "weight_raw": 7, "gw_family": AF_INET, "gateway": "10.60.0.2"},
                        {"ifindex": 13, "weight_raw": 5, "gw_family": AF_INET, "gateway": "10.60.0.3"},
                    ]
                ),
            ],
        ),
    ]
    seed_b = seed.encode("utf-8")
    return b"NLDM" + struct.pack("<HB", 1, len(seed_b)) + seed_b + struct.pack("<I", len(routes)) + b"".join(routes)


def _first_multipath_raw_weights(dump_path: Path) -> list[int]:
    data = dump_path.read_bytes()
    if data[:4] != b"NLDM":
        raise ValueError("bad magic")
    seed_len = data[6]
    pos = 7 + seed_len + 4
    route, _ = parse_route(data[pos:])
    if not route["multipath"]:
        raise ValueError("no multipath")
    return [hop["weight_raw"] for hop in route["multipath"]]


class TestNlctlDecode:
    def setup_method(self) -> None:
        reset()

    def test_protected_dumps_integrity(self) -> None:
        """Fleet dump fixtures under the host catalog must remain unmodified."""
        for name in BUNDLED:
            assert _sha256(DUMPS / name) == PROTECTED_SHA256[name], name

    def test_missing_flags_exit_nonzero(self) -> None:
        """nlctl must reject missing required flags during operational decode."""
        proc = run([CLI, "decode", "--dump", str(DUMPS / BUNDLED[0])])
        assert proc.returncode != 0

    @pytest.mark.parametrize("fixture_name", BUNDLED)
    def test_dump_matches_reference(self, fixture_name: str) -> None:
        """Each fleet catalog dump export must match the independent reference."""
        dump_path = DUMPS / fixture_name
        export = OUTPUT / f"ref-{fixture_name}.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert got == expect

    @pytest.mark.parametrize("fixture_name", BUNDLED)
    def test_bind_snapshot_matches_reference(self, fixture_name: str) -> None:
        """Topology bind snapshot must match the reference bind builder for rollout checks."""
        dump_path = DUMPS / fixture_name
        export = OUTPUT / f"snap-{fixture_name}.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        snap_path = find_bind_snapshot(dump_path)
        actual = json.loads(snap_path.read_text(encoding="utf-8"))
        expected = reference_bind_snapshot(dump_path.read_bytes(), str(dump_path))
        assert actual["version"] == 1
        assert actual["seed"] == expected["seed"]
        assert actual["source_dump"] == expected["source_dump"]
        assert actual["routes"] == expected["routes"]

    @pytest.mark.parametrize("fixture_name", BUNDLED)
    def test_nh_snapshot_matches_reference(self, fixture_name: str) -> None:
        """Host NH snapshot must match the reference NH builder for topology drift witness."""
        dump_path = DUMPS / fixture_name
        export = OUTPUT / f"nh-{fixture_name}.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        bind_path = find_bind_snapshot(dump_path)
        nh_path = find_nh_snapshot(dump_path)
        actual = json.loads(nh_path.read_text(encoding="utf-8"))
        expected = reference_nh_snapshot(
            dump_path.read_bytes(), str(dump_path), str(bind_path)
        )
        assert actual["version"] == 1
        assert actual["seed"] == expected["seed"]
        assert actual["source_dump"] == expected["source_dump"]
        assert actual["bind_snapshot"] == str(bind_path)
        assert actual["snapshot_routes"] == expected["snapshot_routes"]
        assert actual["routes"] == expected["routes"]

    def test_nh_snapshot_routes_sorted_by_id_in_multipath(self) -> None:
        """NH snapshot routes must sort nexthops by ascending id after stage 2a for config order."""
        dump_path = DUMPS / "010-three-hop-priority.bin"
        export = OUTPUT / "nh-sorted.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        nh = json.loads(find_nh_snapshot(dump_path).read_text(encoding="utf-8"))
        ids = [nh["id"] for nh in nh["routes"][0]["nexthops"]]
        assert ids == [1, 2, 3]

    def test_nh_snapshot_snapshot_routes_preserve_bind_order(self) -> None:
        """NH snapshot snapshot_routes must keep bind-stage nexthop encounter order for fleet replay."""
        dump_path = DUMPS / "010-three-hop-priority.bin"
        export = OUTPUT / "nh-bind-order.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        nh = json.loads(find_nh_snapshot(dump_path).read_text(encoding="utf-8"))
        bind = json.loads(find_bind_snapshot(dump_path).read_text(encoding="utf-8"))
        assert nh["snapshot_routes"] == bind["routes"]
        snap_weights = [nh["weight"] for nh in nh["snapshot_routes"][0]["nexthops"]]
        assert snap_weights != sorted(snap_weights)

    def test_export_digest_matches_reference(self) -> None:
        """export_digest must match the independent cross-stage digest builder for rollout seals."""
        dump_path = DUMPS / "001-multipath-v4.bin"
        export = OUTPUT / "digest-ref.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert got["export_digest"] == expect["export_digest"]
        assert len(got["export_digest"]) == 64

    def test_export_digest_binds_snapshot_source_dump(self) -> None:
        """export_digest must incorporate bind snapshot source_dump, not only route rows."""
        dump_path = DUMPS / "001-multipath-v4.bin"
        export = OUTPUT / "digest-source.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        seed, routes = reference_bind_routes(dump_path.read_bytes())
        export_routes = deepcopy(routes)
        for route in export_routes:
            route["nexthops"] = sorted(route["nexthops"], key=lambda nh: nh["id"])
        wrong_dump = compute_export_digest(seed, "/tmp/wrong-path.bin", routes, export_routes)
        assert got["export_digest"] != wrong_dump

    def test_idempotent_export_digest_across_decode_runs(self) -> None:
        """Repeated decode of the same dump must yield identical export_digest."""
        dump_path = DUMPS / "012-route-message-order.bin"
        export_a = OUTPUT / "digest-a.json"
        export_b = OUTPUT / "digest-b.json"
        assert decode(dump_path, export_a).returncode == 0
        assert decode(dump_path, export_b).returncode == 0
        doc_a = json.loads(export_a.read_text(encoding="utf-8"))
        doc_b = json.loads(export_b.read_text(encoding="utf-8"))
        assert doc_a["export_digest"] == doc_b["export_digest"]
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert doc_a["export_digest"] == expect["export_digest"]

    def test_snapshot_source_dump_matches_cli_path(self) -> None:
        """Bind snapshot must record the absolute --dump path passed to nlctl."""
        dump_path = DUMPS / "001-multipath-v4.bin"
        export = OUTPUT / "snap-source.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        snap = json.loads(find_bind_snapshot(dump_path).read_text(encoding="utf-8"))
        assert snap["source_dump"] == str(dump_path)

    def test_multipath_nexthop_ids_restart_per_route(self) -> None:
        """Multipath nexthop ids must restart at 1 for every route in a dump."""
        export = OUTPUT / "nh-scope.json"
        proc = decode(DUMPS / "002-nh-id-scope.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        doc = json.loads(export.read_text(encoding="utf-8"))
        assert len(doc["routes"]) == 2
        for route in doc["routes"]:
            ids = [nh["id"] for nh in route["nexthops"]]
            assert ids == [1, 2]

    def test_nexthops_sorted_ascending(self) -> None:
        """Exported nexthops must be sorted by ascending id per route-contract."""
        export = OUTPUT / "sorted-nh.json"
        proc = decode(DUMPS / "001-multipath-v4.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        doc = json.loads(export.read_text(encoding="utf-8"))
        for route in doc["routes"]:
            ids = [nh["id"] for nh in route["nexthops"]]
            assert ids == sorted(ids)

    def test_metrics_mtu_and_advmss_exported(self) -> None:
        """Both recognized RTA_METRICS nested types must appear on single-path routes."""
        export = OUTPUT / "metrics-both.json"
        proc = decode(DUMPS / "005-metrics-nested.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        nh = json.loads(export.read_text(encoding="utf-8"))["routes"][0]["nexthops"][0]
        assert nh["metrics"] == {"mtu": 1500, "advmss": 1440}

    def test_multipath_ignores_rta_nh_id(self) -> None:
        """RTA_NH_ID must not affect multipath id assignment."""
        export = OUTPUT / "nh-id-ignore.json"
        proc = decode(DUMPS / "009-table-multipath.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        doc = json.loads(export.read_text(encoding="utf-8"))
        ids = [nh["id"] for nh in doc["routes"][0]["nexthops"]]
        assert ids == [1, 2]

    def test_table_override_with_multipath(self) -> None:
        """RTA_TABLE override must win over message table_id on multipath routes."""
        export = OUTPUT / "table-mp.json"
        proc = decode(DUMPS / "009-table-multipath.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))["routes"][0]
        expect = reference_decode((DUMPS / "009-table-multipath.bin").read_bytes())["routes"][0]
        assert got["table"] == 220
        assert got == expect

    def test_seed_weight_scaling_differs_by_dump(self) -> None:
        """Different dump seeds must scale identical raw multipath weights differently."""
        export_a = OUTPUT / "seed-a.json"
        export_b = OUTPUT / "seed-b.json"
        assert decode(DUMPS / "001-multipath-v4.bin", export_a).returncode == 0
        assert decode(DUMPS / "007-alt-seed.bin", export_b).returncode == 0
        doc_a = json.loads(export_a.read_text(encoding="utf-8"))
        doc_b = json.loads(export_b.read_text(encoding="utf-8"))
        weights_a = [nh["weight"] for nh in doc_a["routes"][0]["nexthops"]]
        weights_b = [nh["weight"] for nh in doc_b["routes"][0]["nexthops"]]
        assert doc_a["seed"] != doc_b["seed"]
        assert weights_a != weights_b

    def test_procedural_dump_matches_reference(self) -> None:
        """Runtime-built dump with VERIFIER_SEED must match the reference decoder."""
        dump_path = OUTPUT / "procedural.bin"
        dump_path.write_bytes(write_procedural_dump(PROC_SEED))
        export = OUTPUT / "procedural.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert got == expect

    def test_procedural_chain_bundle(self) -> None:
        """Runtime two-route chain must satisfy export, NH snapshot, and digest together."""
        dump_path = OUTPUT / "procedural-chain.bin"
        dump_path.write_bytes(write_procedural_chain_dump())
        export = OUTPUT / "procedural-chain.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert got == expect
        bind_path = find_bind_snapshot(dump_path)
        nh_path = find_nh_snapshot(dump_path)
        nh_doc = json.loads(nh_path.read_text(encoding="utf-8"))
        expect_nh = reference_nh_snapshot(
            dump_path.read_bytes(), str(dump_path), str(bind_path)
        )
        assert nh_doc == expect_nh

    def test_v6_gateway_uses_minimal_hex_groups(self) -> None:
        """IPv6 gateway must use colon-separated minimal hex groups, not 0.0.0.0 fallback."""
        export = OUTPUT / "v6-gw-groups.json"
        proc = decode(DUMPS / "003-v6-gateway.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_decode((DUMPS / "003-v6-gateway.bin").read_bytes())
        gw = got["routes"][0]["nexthops"][0]["gateway"]
        assert gw == expect["routes"][0]["nexthops"][0]["gateway"]
        assert ":" in gw
        assert gw != "0.0.0.0"
        assert ":000" not in gw

    def test_weight_scaling_formula_from_seed(self) -> None:
        """Multipath weights must follow ((raw * scale) % 255) + 1 with seed-derived scale."""
        export = OUTPUT / "weight-formula.json"
        dump_path = DUMPS / "001-multipath-v4.bin"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        seed = got["seed"]
        got_weights = [nh["weight"] for nh in got["routes"][0]["nexthops"]]
        expect_weights = [nh["weight"] for nh in expect["routes"][0]["nexthops"]]
        assert got_weights == expect_weights
        scale = weight_scale(seed)
        for raw, weight in zip(_first_multipath_raw_weights(dump_path), got_weights):
            assert weight == scaled_weight(seed, raw)
            assert weight == ((raw * scale) % 255) + 1

    def test_export_top_level_keys_only(self) -> None:
        """Export JSON must contain only contract top-level keys."""
        export = OUTPUT / "strict-top.json"
        proc = decode(DUMPS / "006-mixed-dual.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        dump_path = DUMPS / "006-mixed-dual.bin"
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert set(got.keys()) == set(expect.keys())

    def test_v6_multipath_gateways_match_reference(self) -> None:
        """IPv6 multipath hop gateways must decode full 16-byte payloads."""
        export = OUTPUT / "v6-mp.json"
        proc = decode(DUMPS / "008-v6-multipath.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        dump_path = DUMPS / "008-v6-multipath.bin"
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert got == expect

    def test_three_hop_export_sorted_by_id_not_weight(self) -> None:
        """Three-hop multipath must export nexthops by ascending id, not scaled weight."""
        export = OUTPUT / "three-hop-order.json"
        proc = decode(DUMPS / "010-three-hop-priority.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        dump_path = DUMPS / "010-three-hop-priority.bin"
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        route = got["routes"][0]
        ids = [nh["id"] for nh in route["nexthops"]]
        weights = [nh["weight"] for nh in route["nexthops"]]
        assert ids == [1, 2, 3]
        assert weights != sorted(weights)
        assert route["priority"] == 500
        assert route["table"] == 190
        assert got == expect

    def test_bind_snapshot_preserves_unscaled_weight_order(self) -> None:
        """Bind snapshot must not pre-sort nexthops by scaled weight (export_nh sorts by id)."""
        dump_path = DUMPS / "010-three-hop-priority.bin"
        export = OUTPUT / "snap-weight-order.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        snap = json.loads(find_bind_snapshot(dump_path).read_text(encoding="utf-8"))
        weights = [nh["weight"] for nh in snap["routes"][0]["nexthops"]]
        assert weights != sorted(weights)

    def test_partial_golden_decode_bind_export_still_wrong_nh_order(self) -> None:
        """Golden decode and bind with broken export_nh still mis-orders nexthops."""
        def check() -> None:
            dump_path = DUMPS / "010-three-hop-priority.bin"
            export = OUTPUT / "partial-export-nh.json"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got != expect
            assert [nh["id"] for nh in got["routes"][0]["nexthops"]] != [1, 2, 3]

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "bind.rs": GOLDEN / "bind.rs",
            },
            check,
        )

    def test_partial_golden_decode_bind_export_still_wrong_nh_snapshot(self) -> None:
        """Golden decode, bind, and export with broken export_nh still corrupts NH snapshot."""
        def check() -> None:
            dump_path = DUMPS / "010-three-hop-priority.bin"
            export = OUTPUT / "partial-nh-snap.json"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            bind_path = find_bind_snapshot(dump_path)
            nh_path = find_nh_snapshot(dump_path)
            got_nh = json.loads(nh_path.read_text(encoding="utf-8"))
            expect_nh = reference_nh_snapshot(
                dump_path.read_bytes(), str(dump_path), str(bind_path)
            )
            assert got_nh != expect_nh
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got != expect

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "bind.rs": GOLDEN / "bind.rs",
                "export.rs": GOLDEN / "export.rs",
            },
            check,
        )

    def test_partial_golden_decode_only_still_wrong_table_override(self) -> None:
        """Fixing only decode.rs still binds with inverted table override logic."""
        def check() -> None:
            export = OUTPUT / "partial-decode.json"
            proc = decode(DUMPS / "004-table-override.bin", export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode((DUMPS / "004-table-override.bin").read_bytes())
            assert got != expect

        with_partial_patch({"decode.rs": GOLDEN / "decode.rs"}, check)

    def test_partial_golden_bind_only_still_wrong_v6_gateway(self) -> None:
        """Fixing only bind.rs still decodes truncated IPv6 gateway payloads."""
        def check() -> None:
            export = OUTPUT / "partial-bind.json"
            proc = decode(DUMPS / "003-v6-gateway.bin", export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode((DUMPS / "003-v6-gateway.bin").read_bytes())
            assert got != expect

        with_partial_patch({"bind.rs": GOLDEN / "bind.rs"}, check)

    def test_partial_golden_decode_bind_still_wrong_export_order(self) -> None:
        """Golden decode and bind with broken export_nh still sorts nexthops by weight."""
        def check() -> None:
            dump_path = DUMPS / "010-three-hop-priority.bin"
            export = OUTPUT / "partial-export.json"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got != expect
            assert [nh["id"] for nh in got["routes"][0]["nexthops"]] != [1, 2, 3]

        with_partial_patch(
            {"decode.rs": GOLDEN / "decode.rs", "bind.rs": GOLDEN / "bind.rs"},
            check,
        )

    def test_partial_bind_snapshot_weight_sort_still_fails(self) -> None:
        """Golden decode with snapshot nexthops sorted by weight must not match reference snapshot."""
        partial = TEST_DIR / "broken_bind_snapshot_weight_partial.rs"

        def check() -> None:
            dump_path = DUMPS / "010-three-hop-priority.bin"
            export = OUTPUT / "partial-snap-weight.json"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            snap = json.loads(find_bind_snapshot(dump_path).read_text(encoding="utf-8"))
            expect_snap = reference_bind_snapshot(dump_path.read_bytes(), str(dump_path))
            assert snap["routes"] != expect_snap["routes"]
            assert [nh["id"] for nh in snap["routes"][0]["nexthops"]] != [1, 2, 3]

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "bind.rs": partial,
            },
            check,
        )

    def test_partial_golden_export_only_still_wrong_weights(self) -> None:
        """Fixing only export.rs still leaves bind weight scaling wrong on multipath."""
        def check() -> None:
            export = OUTPUT / "partial-export-weights.json"
            dump_path = DUMPS / "001-multipath-v4.bin"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got != expect
            got_weights = [nh["weight"] for nh in got["routes"][0]["nexthops"]]
            expect_weights = [nh["weight"] for nh in expect["routes"][0]["nexthops"]]
            assert got_weights != expect_weights

        with_partial_patch({"export.rs": GOLDEN / "export.rs"}, check)

    def test_partial_golden_decode_bind_nh_still_wrong_export_digest(self) -> None:
        """Golden decode/bind/export_nh with seed-only digest still fails export contract."""
        def check() -> None:
            dump_path = DUMPS / "001-multipath-v4.bin"
            export = OUTPUT / "partial-digest.json"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got["routes"] == expect["routes"]
            assert got["export_digest"] != expect["export_digest"]
            assert got != expect

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "bind.rs": GOLDEN / "bind.rs",
                "export_nh.rs": GOLDEN / "export_nh.rs",
                "export.rs": BROKEN / "export_wrong_digest.rs",
            },
            check,
        )

    def test_partial_golden_export_only_still_wrong_export_digest(self) -> None:
        """Fixing only export.rs still leaves bind scaling wrong and digest mismatched."""
        def check() -> None:
            export = OUTPUT / "partial-export-digest.json"
            dump_path = DUMPS / "001-multipath-v4.bin"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got != expect
            assert got["export_digest"] != expect["export_digest"]

        with_partial_patch({"export.rs": GOLDEN / "export.rs"}, check)

    def test_v6_dst_minimal_hex_groups(self) -> None:
        """IPv6 destination must use minimal hex groups, not zero-padded width-four groups."""
        export = OUTPUT / "v6-dst-minimal.json"
        proc = decode(DUMPS / "011-v6-dst-minimal.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        dump_path = DUMPS / "011-v6-dst-minimal.bin"
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        dst = got["routes"][0]["dst"]
        assert dst == expect["routes"][0]["dst"]
        assert ":000" not in dst
        assert got == expect

    def test_routes_preserve_dump_message_order(self) -> None:
        """Routes must stay in binary message order, not sorted by table id."""
        export = OUTPUT / "route-order.json"
        proc = decode(DUMPS / "012-route-message-order.bin", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        dump_path = DUMPS / "012-route-message-order.bin"
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert [route["table"] for route in got["routes"]] == [300, 100]
        assert got == expect

    def test_multipath_route_metrics_not_on_nexthops(self) -> None:
        """Route-level RTA_METRICS on multipath routes must not attach to nexthop rows."""
        dump_path = DUMPS / "014-multipath-metrics-isolated.bin"
        export = OUTPUT / "mp-metrics-isolated.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert got == expect
        for nh in got["routes"][0]["nexthops"]:
            assert "metrics" not in nh

    def test_partial_golden_decode_guard_rejects_multipath_metrics_leak(self) -> None:
        """Golden decode with metrics leak on bind must fail stage-1b guard before export."""
        def check() -> None:
            dump_path = DUMPS / "014-multipath-metrics-isolated.bin"
            export = OUTPUT / "partial-guard-metrics.json"
            proc = decode(dump_path, export)
            assert proc.returncode != 0, proc.stdout + proc.stderr

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "snapshot_guard.rs": GOLDEN / "snapshot_guard.rs",
            },
            check,
        )

    def test_partial_golden_decode_bind_nh_still_leaks_metrics_without_guard(self) -> None:
        """Golden decode/bind/nh with broken guard still exports metrics on multipath hops."""
        def check() -> None:
            dump_path = DUMPS / "014-multipath-metrics-isolated.bin"
            export = OUTPUT / "partial-leak-metrics.json"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got != expect
            assert "metrics" in got["routes"][0]["nexthops"][0]

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "export_nh.rs": GOLDEN / "export_nh.rs",
                "export.rs": GOLDEN / "export.rs",
            },
            check,
        )

    def test_partial_golden_export_nh_only_still_wrong_route_order(self) -> None:
        """Golden bind snapshot with golden export_nh but route table sort in export still fails."""
        def check() -> None:
            export = OUTPUT / "partial-export-order.json"
            proc = decode(DUMPS / "012-route-message-order.bin", export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode((DUMPS / "012-route-message-order.bin").read_bytes())
            assert got != expect
            assert [route["table"] for route in got["routes"]] == [100, 300]

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "bind.rs": GOLDEN / "bind.rs",
                "export.rs": BROKEN / "export_route_table_sort.rs",
                "export_nh.rs": GOLDEN / "export_nh.rs",
            },
            check,
        )

    def test_tb3_hidden_cross_stage_chain(self) -> None:
        """Hidden two-route chain must satisfy guard, NH snapshot_routes, and export_digest."""
        dump_path = OUTPUT / "tb3-cross-stage.bin"
        dump_path.write_bytes(write_tb3_hidden_cross_stage_dump())
        export = OUTPUT / "tb3-cross-stage.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert got == expect
        bind_path = find_bind_snapshot(dump_path)
        nh_path = find_nh_snapshot(dump_path)
        nh_doc = json.loads(nh_path.read_text(encoding="utf-8"))
        bind_doc = json.loads(bind_path.read_text(encoding="utf-8"))
        expect_nh = reference_nh_snapshot(
            dump_path.read_bytes(), str(dump_path), str(bind_path)
        )
        assert nh_doc == expect_nh
        assert nh_doc["snapshot_routes"] == bind_doc["routes"]
        assert got["export_digest"] == expect["export_digest"]

    def test_tb3_hidden_single_path_metrics_passes_guard(self) -> None:
        """Hidden single-path metrics route must pass stage-1b guard and export."""
        dump_path = OUTPUT / "tb3-guard-metrics.bin"
        dump_path.write_bytes(write_tb3_hidden_guard_metrics_dump())
        export = OUTPUT / "tb3-guard-metrics.json"
        proc = decode(dump_path, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_decode(dump_path.read_bytes(), str(dump_path))
        assert got == expect
        assert got["routes"][0]["nexthops"][0]["metrics"] == {"mtu": 1500}

    def test_cross_run_nh_ids_reset_between_invocations(self) -> None:
        """Multipath ids must restart at 1 on each decode invocation, not accumulate."""
        export_a = OUTPUT / "cross-run-a.json"
        export_b = OUTPUT / "cross-run-b.json"
        assert decode(DUMPS / "013-dual-multipath-nh-chain.bin", export_a).returncode == 0
        assert decode(DUMPS / "001-multipath-v4.bin", export_b).returncode == 0
        doc_b = json.loads(export_b.read_text(encoding="utf-8"))
        ids = [nh["id"] for nh in doc_b["routes"][0]["nexthops"]]
        assert ids == [1, 2]

    def test_partial_golden_route_table_digest_trap(self) -> None:
        """Golden decode/bind/nh with legacy route_table_digest export still fails digest."""
        def check() -> None:
            dump_path = DUMPS / "001-multipath-v4.bin"
            export = OUTPUT / "partial-legacy-digest.json"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got["routes"] == expect["routes"]
            assert got["export_digest"] != expect["export_digest"]

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "bind.rs": GOLDEN / "bind.rs",
                "export_nh.rs": GOLDEN / "export_nh.rs",
                "snapshot_guard.rs": GOLDEN / "snapshot_guard.rs",
            },
            check,
        )

    def test_partial_golden_snapshot_routes_weight_sort_still_wrong_digest(self) -> None:
        """Golden export with broken export_nh snapshot_routes sort corrupts export_digest."""
        def check() -> None:
            dump_path = DUMPS / "010-three-hop-priority.bin"
            export = OUTPUT / "partial-snap-routes-sort.json"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            nh_path = find_nh_snapshot(dump_path)
            got_nh = json.loads(nh_path.read_text(encoding="utf-8"))
            bind_path = find_bind_snapshot(dump_path)
            bind_doc = json.loads(bind_path.read_text(encoding="utf-8"))
            assert got_nh["snapshot_routes"] != bind_doc["routes"]
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got["export_digest"] != expect["export_digest"]

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "bind.rs": GOLDEN / "bind.rs",
                "export.rs": GOLDEN / "export.rs",
                "snapshot_guard.rs": GOLDEN / "snapshot_guard.rs",
            },
            check,
        )

    def test_partial_golden_guard_inverted_rejects_valid_single_path(self) -> None:
        """Golden decode with inverted guard must reject valid single-path metrics routes."""
        def check() -> None:
            dump_path = OUTPUT / "partial-guard-invert.bin"
            dump_path.write_bytes(write_tb3_hidden_guard_metrics_dump())
            export = OUTPUT / "partial-guard-invert.json"
            proc = decode(dump_path, export)
            assert proc.returncode != 0, proc.stdout + proc.stderr

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "bind.rs": GOLDEN / "bind.rs",
            },
            check,
        )

    def test_partial_golden_bind_guard_nh_still_wrong_tb3_hidden(self) -> None:
        """Golden bind/guard/nh with broken export_nh snapshot_routes sort fails hidden TB3."""
        def check() -> None:
            dump_path = OUTPUT / "partial-tb3-snap-sort.bin"
            dump_path.write_bytes(write_tb3_hidden_cross_stage_dump())
            export = OUTPUT / "partial-tb3-snap-sort.json"
            proc = decode(dump_path, export)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_decode(dump_path.read_bytes(), str(dump_path))
            assert got != expect

        with_partial_patch(
            {
                "decode.rs": GOLDEN / "decode.rs",
                "bind.rs": GOLDEN / "bind.rs",
                "snapshot_guard.rs": GOLDEN / "snapshot_guard.rs",
                "export.rs": GOLDEN / "export.rs",
            },
            check,
        )
