"""Behavioral verifier for collectdctl ingest pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest

APP = Path("/app")
CONFIG = APP / "config" / "ingest.json"
BATCHES = APP / "fixtures" / "batches"
OUTPUT = APP / "output"
STAGING = APP / "state" / "collectd-ingest.snapshot.json"
CLI = "collectdctl"
RESET = APP / "scripts" / "reset-state.sh"
SEED = os.environ.get("VERIFIER_SEED", "collectd-seed-160")
TESTS_DIR = Path(__file__).resolve().parent
PATCHES = TESTS_DIR / "patches"
BROKEN = TESTS_DIR / "broken_lib"

PATCH_TARGETS = {
    "putval": APP / "internal/parse/putval.go",
    "types": APP / "internal/parse/types.go",
    "escape": APP / "internal/normalize/escape.go",
    "derive": APP / "internal/normalize/derive.go",
    "batch": APP / "internal/flush/batch.go",
    "skew": APP / "internal/flush/skew.go",
    "staging": APP / "internal/staging/staging.go",
    "export": APP / "internal/export/report.go",
}

BUNDLED = [
    "001-gauge-basic.txt",
    "002-derive-pair.txt",
    "003-escaped-slash.txt",
    "004-flush-boundary.txt",
    "005-skew-edge.txt",
    "006-mixed-types.txt",
    "007-counter-wrap.txt",
]

PROTECTED_SHA256: dict[str, str] = {
    "001-gauge-basic.txt": "c26d3bdcc264762ce1e58e327b00de920fbbaba4458586338e97c6639ae5fc9a",
    "002-derive-pair.txt": "0a0419bea1850ae8d1e300d5468daca00338ae40dbbc49c70ec73e9765d7668e",
    "003-escaped-slash.txt": "0f94b4af6a93a2a58dcb12d3c5799aeb429da6238f922ab97afb8ff98da04dbe",
    "004-flush-boundary.txt": "d5b6dbedaa0656faedf4eaed75802896e0ad48c3fa7c0b5d50075373f873fad8",
    "005-skew-edge.txt": "d9ffdf42b52e98e42f0f4cea79b528d592b326cc6d6e2d97cec1fdee6921cb5d",
    "006-mixed-types.txt": "eb493258f783c3cbed28f76f93e52cb561c0dd076412525bd23c596c071e3f80",
    "007-counter-wrap.txt": "1afdc6809a9c33090bb3a994e38d0615e19bec7330cc867f82a8824d132a621c",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def ingest(text_path: Path | None, export_path: Path) -> subprocess.CompletedProcess[str]:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [CLI, "ingest", "--config", str(CONFIG), "--output", str(export_path)]
    if text_path is not None:
        cmd.extend(["--text", str(text_path)])
    return run(cmd)


def stage(text_path: Path | None) -> subprocess.CompletedProcess[str]:
    cmd = [CLI, "stage", "--config", str(CONFIG)]
    if text_path is not None:
        cmd.extend(["--text", str(text_path)])
    return run(cmd)


def export_out(export_path: Path) -> subprocess.CompletedProcess[str]:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    return run([CLI, "export", "--output", str(export_path)])


def build_cli() -> None:
    proc = run(["go", "build", "-mod=readonly", "-o", "/usr/local/bin/collectdctl", "./cmd/collectdctl"])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _snapshot_sources() -> dict[str, str]:
    return {name: path.read_text(encoding="utf-8") for name, path in PATCH_TARGETS.items()}


def _restore_sources(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        PATCH_TARGETS[name].write_text(content, encoding="utf-8")


def _restore_broken_sources() -> None:
    for name, dest in PATCH_TARGETS.items():
        shutil.copyfile(BROKEN / f"{name}.go", dest)


def _install_patch(name: str) -> None:
    shutil.copyfile(PATCHES / f"golden_{name}.go", PATCH_TARGETS[name])


def assert_mismatch_or_missing(proc: subprocess.CompletedProcess[str], expected: dict, out: Path) -> None:
    if proc.returncode != 0 or not out.is_file():
        return
    got = json.loads(out.read_text(encoding="utf-8"))
    if got != expected:
        return
    raise AssertionError("partial patch produced full reference output")


@contextmanager
def _patched_modules(*names: str):
    saved = _snapshot_sources()
    try:
        _restore_broken_sources()
        for name in names:
            _install_patch(name)
        build_cli()
        yield
    finally:
        _restore_sources(saved)
        build_cli()


@contextmanager
def _patched_module(name: str):
    with _patched_modules(name):
        yield


def select_batches(seed: str, batches: list[str]) -> list[str]:
    digest = hashlib.sha256(seed.encode()).digest()
    bits = digest[0] | (digest[1] << 8)
    limit = min(len(batches), 16)
    selected = [batches[i] for i in range(limit) if (bits >> i) & 1]
    if not selected:
        selected = [batches[digest[2] % len(batches)]]
    out = list(selected)
    for i in range(len(out) - 1, 0, -1):
        j = digest[i % len(digest)] % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out


@dataclass
class ValueGroup:
    epoch: int
    values: list[float]


@dataclass
class RawReading:
    identifier: str
    interval: int
    groups: list[ValueGroup]


@dataclass
class Point:
    canonical_id: str
    ds: str
    value_kind: str
    epoch: int
    value: float


def read_identifier(rest: str) -> tuple[str, str]:
    rest = rest.strip()
    if not rest:
        raise ValueError("missing identifier")
    if rest[0] == '"':
        chars: list[str] = []
        escaped = False
        i = 1
        while i < len(rest):
            ch = rest[i]
            if escaped:
                chars.append("/" if ch == "/" else "\\" + ch)
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                return "".join(chars), rest[i + 1 :].strip()
            else:
                chars.append(ch)
            i += 1
        raise ValueError("bad quoted identifier")
    end = 0
    while end < len(rest) and not rest[end].isspace():
        end += 1
    return rest[:end], rest[end:].strip()


def parse_value_groups(tail: str) -> list[ValueGroup]:
    groups: list[ValueGroup] = []
    for part in tail.split():
        fields = part.split(":")
        epoch = int(fields[0])
        values = [float(v) for v in fields[1:]]
        groups.append(ValueGroup(epoch=epoch, values=values))
    return groups


def parse_line(line: str) -> RawReading:
    line = line.strip()
    if not line.startswith("PUTVAL "):
        raise ValueError("bad putval")
    rest = line[len("PUTVAL ") :].strip()
    identifier, tail = read_identifier(rest)
    interval = 10
    while tail.startswith("interval="):
        field, tail = (tail.split(" ", 1) + [""])[:2]
        interval = int(field.split("=", 1)[1])
        tail = tail.strip()
    return RawReading(identifier=identifier, interval=interval, groups=parse_value_groups(tail))


def parse_stream(text: str) -> list[RawReading]:
    out: list[RawReading] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(parse_line(line))
    return out


def type_name(identifier: str) -> str:
    parts = identifier.split("/")
    if len(parts) < 3:
        return ""
    base = parts[2]
    if "-" in base:
        base = base.split("-", 1)[0]
    return base


def canonical_id(identifier: str) -> str:
    ident = identifier.strip()
    if len(ident) >= 2 and ident[0] == '"' and ident[-1] == '"':
        ident = ident[1:-1]
    return ident.replace(r"\/", "/")


def ordered_ds(type_name_value: str, types_db: dict) -> list[str]:
    ds_map = types_db.get(type_name_value)
    if not ds_map:
        return []
    return sorted(ds_map.keys())


def export_kind(kind: str) -> str:
    return {
        "derive": "derive_rate",
        "counter": "counter_delta",
        "absolute": "absolute",
    }.get(kind, "gauge")


def expand_readings(raw: RawReading, types_db: dict) -> list[Point]:
    canon = canonical_id(raw.identifier)
    tname = type_name(canon)
    ds_names = ordered_ds(tname, types_db)
    if not ds_names:
        return []
    out: list[Point] = []
    for group in raw.groups:
        for i, val in enumerate(group.values):
            if i >= len(ds_names):
                break
            kind = types_db[tname][ds_names[i]]
            out.append(
                Point(
                    canonical_id=canon,
                    ds=ds_names[i],
                    value_kind=export_kind(kind),
                    epoch=group.epoch,
                    value=val,
                )
            )
    return out


def pair_rates(points: list[Point], kind: str) -> list[Point]:
    if len(points) < 2 or kind not in {"derive", "counter"}:
        return points
    ordered = sorted(points, key=lambda p: p.epoch)
    p1, p2 = ordered[-2], ordered[-1]
    dt = p2.epoch - p1.epoch
    if dt <= 0:
        return points
    delta = p2.value - p1.value
    if kind == "counter":
        if delta < 0:
            delta = (1 << 32) - p1.value + p2.value
        return [
            Point(p2.canonical_id, p2.ds, "counter_delta", p2.epoch, delta),
        ]
    if delta < 0:
        delta += 1 << 32
    return [Point(p2.canonical_id, p2.ds, "derive_rate", p2.epoch, delta / dt)]


def flush_index(epoch: int, origin: int, interval_sec: int) -> int:
    if epoch < origin:
        return -1
    return (epoch - origin) // interval_sec


def within_skew(epoch: int, anchor: int, skew_sec: int) -> bool:
    if anchor < 0:
        return True
    diff = abs(epoch - anchor)
    return diff <= skew_sec


def reference_ingest(texts: list[str], cfg: dict, batch_names: list[str]) -> dict:
    types_db = cfg["types_db"]
    origin = int(cfg["epoch_origin"])
    interval = int(cfg["flush_interval_sec"])
    skew = int(cfg["time_skew_sec"])

    stats = {"lines": 0, "accepted": 0, "rejected": 0}
    series: dict[tuple[str, str], list[Point]] = {}

    for content in texts:
        anchor = -1
        readings = parse_stream(content)
        stats["lines"] += len(readings)
        for raw in readings:
            for pt in expand_readings(raw, types_db):
                if pt.epoch < origin:
                    stats["rejected"] += 1
                    continue
                if anchor < 0:
                    anchor = pt.epoch
                if not within_skew(pt.epoch, anchor, skew):
                    stats["rejected"] += 1
                    continue
                stats["accepted"] += 1
                key = (pt.canonical_id, pt.ds)
                series.setdefault(key, []).append(pt)

    flushes: dict[int, list[dict]] = {}
    for (canon, ds), pts in series.items():
        kind = types_db[type_name(canon)][ds]
        for pt in pair_rates(pts, kind):
            idx = flush_index(pt.epoch, origin, interval)
            if idx < 0:
                continue
            flushes.setdefault(idx, []).append(
                {
                    "canonical_id": pt.canonical_id,
                    "ds": pt.ds,
                    "value_kind": pt.value_kind,
                    "epoch": pt.epoch,
                    "value": pt.value,
                }
            )

    out_flushes = []
    for idx in sorted(flushes):
        metrics = sorted(flushes[idx], key=lambda m: (m["canonical_id"], m["ds"], m["epoch"]))
        start = origin + idx * interval
        end = start + interval
        out_flushes.append(
            {
                "flush_index": idx,
                "start_epoch": start,
                "end_epoch": end,
                "metrics": metrics,
            }
        )

    return {
        "pipeline_version": 1,
        "seed": cfg["seed"],
        "batches": batch_names,
        "flushes": out_flushes,
        "stats": stats,
    }


def reference_binding(report: dict) -> str:
    parts = [
        report["seed"],
        "\n".join(report["batches"]),
        str(report["pipeline_version"]),
        str(report["stats"]["lines"]),
        str(report["stats"]["accepted"]),
        str(report["stats"]["rejected"]),
    ]
    for flush in report["flushes"]:
        parts.append(str(flush["flush_index"]))
        parts.append(str(flush["start_epoch"]))
        parts.append(str(flush["end_epoch"]))
        for metric in flush["metrics"]:
            ordered = {
                "canonical_id": metric["canonical_id"],
                "ds": metric["ds"],
                "value_kind": metric["value_kind"],
                "epoch": metric["epoch"],
                "value": metric["value"],
            }
            parts.append(json.dumps(ordered, separators=(",", ":")))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


class TestCollectdctlIngest:
    def setup_method(self) -> None:
        reset()

    def test_protected_batches_integrity(self) -> None:
        """Bundled PUTVAL fixtures must remain unmodified."""
        for name in BUNDLED:
            assert _sha256(BATCHES / name) == PROTECTED_SHA256[name], name

    @pytest.mark.parametrize("fixture_name", BUNDLED)
    def test_batch_matches_reference(self, fixture_name: str) -> None:
        """Each catalog batch export must match the independent reference pipeline."""
        export = OUTPUT / f"ref-{fixture_name}.json"
        proc = ingest(BATCHES / fixture_name, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        cfg = load_config()
        text = (BATCHES / fixture_name).read_text(encoding="utf-8")
        expect = reference_ingest([text], cfg, [fixture_name])
        assert got == expect

    def test_escaped_slash_identifier(self) -> None:
        """Quoted identifiers must unescape embedded slashes before validation."""
        export = OUTPUT / "escaped.json"
        assert ingest(BATCHES / "003-escaped-slash.txt", export).returncode == 0
        doc = json.loads(export.read_text(encoding="utf-8"))
        metric = doc["flushes"][0]["metrics"][0]
        assert metric["canonical_id"] == "edge/rack01/cpu-0/cpu-idle"
        assert metric["value"] == 12.5

    def test_derive_rate_computation(self) -> None:
        """Derive data sources must export per-second rates, not raw counter values."""
        export = OUTPUT / "derive.json"
        assert ingest(BATCHES / "002-derive-pair.txt", export).returncode == 0
        doc = json.loads(export.read_text(encoding="utf-8"))
        by_ds = {(m["canonical_id"], m["ds"]): m for f in doc["flushes"] for m in f["metrics"]}
        assert by_ds[("beta/if-eth0/if_octets", "rx")]["value_kind"] == "derive_rate"
        assert by_ds[("beta/if-eth0/if_octets", "rx")]["value"] == 750.0
        assert by_ds[("beta/if-eth0/if_octets", "tx")]["value"] == 150.0

    def test_flush_boundary_assignment(self) -> None:
        """Epochs on flush window edges must land in distinct flush indices."""
        export = OUTPUT / "boundary.json"
        assert ingest(BATCHES / "004-flush-boundary.txt", export).returncode == 0
        doc = json.loads(export.read_text(encoding="utf-8"))
        assert {f["flush_index"] for f in doc["flushes"]} == {0, 1}

    def test_skew_buffer_inclusive_edge(self) -> None:
        """Skew buffer must accept anchor+skew and reject anchor+skew+1 per batch file."""
        export = OUTPUT / "skew.json"
        assert ingest(BATCHES / "005-skew-edge.txt", export).returncode == 0
        doc = json.loads(export.read_text(encoding="utf-8"))
        assert doc["stats"] == {"lines": 3, "accepted": 4, "rejected": 2}
        epochs = {m["epoch"] for f in doc["flushes"] for m in f["metrics"]}
        assert 1704067203 in epochs
        assert 1704067204 not in epochs

    def test_counter_wrap_delta(self) -> None:
        """Counter deltas must handle uint32 wrap across paired epochs."""
        export = OUTPUT / "wrap.json"
        assert ingest(BATCHES / "007-counter-wrap.txt", export).returncode == 0
        doc = json.loads(export.read_text(encoding="utf-8"))
        metric = doc["flushes"][0]["metrics"][0]
        assert metric["value_kind"] == "counter_delta"
        assert metric["value"] == 11.0

    def test_seed_bundle_matches_reference(self) -> None:
        """Full-seed multi-batch ingest must match reference selection and matrix."""
        export = OUTPUT / "bundle.json"
        proc = ingest(None, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        cfg = load_config()
        names = select_batches(cfg["seed"], cfg["batches"])
        texts = [(BATCHES / name).read_text(encoding="utf-8") for name in names]
        expect = reference_ingest(texts, cfg, names)
        assert got == expect
        assert len(names) == 7

    def test_seed_subset_order_differs(self) -> None:
        """Subset seed must permute batches differently from the bundled verifier seed."""
        subset_seed = "collectd-seed-11"
        export = OUTPUT / "subset.json"
        cfg = load_config()
        subset_cfg = dict(cfg)
        subset_cfg["seed"] = subset_seed
        subset_path = OUTPUT / "subset-config.json"
        subset_path.write_text(json.dumps(subset_cfg, indent=2) + "\n", encoding="utf-8")
        proc = run(
            [
                CLI,
                "ingest",
                "--config",
                str(subset_path),
                "--output",
                str(export),
            ]
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        names = select_batches(subset_seed, cfg["batches"])
        texts = [(BATCHES / name).read_text(encoding="utf-8") for name in names]
        expect = reference_ingest(texts, subset_cfg, names)
        assert got == expect
        assert len(names) == 2
        assert names != select_batches(SEED, cfg["batches"])

    def test_stage_writes_staging_snapshot(self) -> None:
        """Stage must persist the collectd ingest staging envelope."""
        reset()
        proc = stage(BATCHES / "001-gauge-basic.txt")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert STAGING.is_file(), "collectd-ingest.snapshot.json missing"
        envelope = json.loads(STAGING.read_text(encoding="utf-8"))
        assert isinstance(envelope.get("ingest_binding"), str) and envelope["ingest_binding"]
        assert isinstance(envelope.get("report"), dict)
        assert envelope["report"]["batches"] == ["001-gauge-basic.txt"]

    def test_export_without_stage_fails(self) -> None:
        """Export must fail when no staging snapshot exists."""
        reset()
        proc = export_out(OUTPUT / "no-staging.json")
        assert proc.returncode == 2

    def test_stage_then_export_matches_ingest(self) -> None:
        """Split stage/export must match combined ingest output."""
        fixture = "006-mixed-types.txt"
        out = OUTPUT / "split-mixed-types.json"
        cfg = load_config()
        text = (BATCHES / fixture).read_text(encoding="utf-8")
        want = reference_ingest([text], cfg, [fixture])
        assert stage(BATCHES / fixture).returncode == 0
        proc = export_out(out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        assert got == want

    def test_staging_preserves_metric_order(self) -> None:
        """Metric rows must stay in contract order through stage/export."""
        fixture = "002-derive-pair.txt"
        out = OUTPUT / "split-derive-pair.json"
        cfg = load_config()
        text = (BATCHES / fixture).read_text(encoding="utf-8")
        want = reference_ingest([text], cfg, [fixture])
        assert stage(BATCHES / fixture).returncode == 0
        assert export_out(out).returncode == 0
        got = json.loads(out.read_text(encoding="utf-8"))
        assert got["flushes"] == want["flushes"]

    def test_export_reads_staging_not_reingest(self) -> None:
        """Export must publish staged metric values without re-parsing batch files."""
        fixture = "001-gauge-basic.txt"
        assert stage(BATCHES / fixture).returncode == 0
        envelope = json.loads(STAGING.read_text(encoding="utf-8"))
        tampered = -4242
        envelope["report"]["flushes"][0]["metrics"][0]["value"] = tampered
        envelope["ingest_binding"] = reference_binding(envelope["report"])
        STAGING.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")
        out = OUTPUT / "staging-tamper-export.json"
        assert export_out(out).returncode == 0, "export should publish staged snapshot rows"
        got = json.loads(out.read_text(encoding="utf-8"))
        assert got["flushes"][0]["metrics"][0]["value"] == tampered

    def test_hidden_seed_bundle_matches_reference(self) -> None:
        """Hidden seed must select a different batch subset than the bundled verifier seed."""
        hidden_seed = "collectd-seed-77"
        export = OUTPUT / "hidden-seed-bundle.json"
        cfg = load_config()
        hidden_cfg = dict(cfg)
        hidden_cfg["seed"] = hidden_seed
        hidden_path = OUTPUT / "hidden-config.json"
        hidden_path.write_text(json.dumps(hidden_cfg, indent=2) + "\n", encoding="utf-8")
        proc = run(
            [
                CLI,
                "ingest",
                "--config",
                str(hidden_path),
                "--output",
                str(export),
            ]
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        names = select_batches(hidden_seed, cfg["batches"])
        texts = [(BATCHES / name).read_text(encoding="utf-8") for name in names]
        expect = reference_ingest(texts, hidden_cfg, names)
        assert got == expect
        assert names != select_batches(SEED, cfg["batches"])
        assert len(names) == 4

    @pytest.mark.parametrize("module", ["putval", "derive", "batch", "skew", "staging", "export"])
    def test_partial_fix_still_fails_bundled(self, module: str) -> None:
        """Fixing only one module must not satisfy every bundled batch."""
        with _patched_module(module):
            mismatches = 0
            for fixture_name in BUNDLED:
                export = OUTPUT / f"partial-{module}-{fixture_name}.json"
                proc = ingest(BATCHES / fixture_name, export)
                if proc.returncode != 0:
                    mismatches += 1
                    continue
                cfg = load_config()
                text = (BATCHES / fixture_name).read_text(encoding="utf-8")
                expect = reference_ingest([text], cfg, [fixture_name])
                got = json.loads(export.read_text(encoding="utf-8"))
                if got != expect:
                    mismatches += 1
            assert mismatches > 0, f"partial {module} patch matched every bundled batch"

    def test_partial_putval_only_still_fails_derive_pair(self) -> None:
        """Golden putval alone must not export derive rates."""
        export = OUTPUT / "partial-putval-derive.json"
        cfg = load_config()
        text = (BATCHES / "002-derive-pair.txt").read_text(encoding="utf-8")
        want = reference_ingest([text], cfg, ["002-derive-pair.txt"])
        with _patched_module("putval"):
            proc = ingest(BATCHES / "002-derive-pair.txt", export)
            assert_mismatch_or_missing(proc, want, export)

    def test_partial_derive_only_still_fails_counter_wrap(self) -> None:
        """Golden derive alone must not handle counter wrap deltas."""
        export = OUTPUT / "partial-derive-wrap.json"
        cfg = load_config()
        text = (BATCHES / "007-counter-wrap.txt").read_text(encoding="utf-8")
        want = reference_ingest([text], cfg, ["007-counter-wrap.txt"])
        with _patched_module("derive"):
            proc = ingest(BATCHES / "007-counter-wrap.txt", export)
            assert_mismatch_or_missing(proc, want, export)

    def test_partial_staging_only_still_fails_split_export(self) -> None:
        """Golden staging alone must not satisfy split stage/export metric order."""
        export = OUTPUT / "partial-staging-split.json"
        cfg = load_config()
        text = (BATCHES / "006-mixed-types.txt").read_text(encoding="utf-8")
        want = reference_ingest([text], cfg, ["006-mixed-types.txt"])
        with _patched_module("staging"):
            stage(BATCHES / "006-mixed-types.txt")
            proc = export_out(export)
            assert_mismatch_or_missing(proc, want, export)

    def test_partial_export_only_still_fails_metric_order(self) -> None:
        """Golden export alone must not preserve canonical metric ordering."""
        export = OUTPUT / "partial-export-order.json"
        cfg = load_config()
        text = (BATCHES / "002-derive-pair.txt").read_text(encoding="utf-8")
        want = reference_ingest([text], cfg, ["002-derive-pair.txt"])
        with _patched_module("export"):
            stage(BATCHES / "002-derive-pair.txt")
            proc = export_out(export)
            assert_mismatch_or_missing(proc, want, export)

    def test_partial_putval_derive_still_fails_split_pipeline(self) -> None:
        """Parse and derive fixes without staging/export still break stage/export."""
        export = OUTPUT / "partial-putval-derive-split.json"
        cfg = load_config()
        text = (BATCHES / "006-mixed-types.txt").read_text(encoding="utf-8")
        want = reference_ingest([text], cfg, ["006-mixed-types.txt"])
        with _patched_modules("putval", "derive", "batch", "skew"):
            stage(BATCHES / "006-mixed-types.txt")
            proc = export_out(export)
            assert_mismatch_or_missing(proc, want, export)

    def test_partial_putval_derive_export_still_fails_ingest_binding(self) -> None:
        """Wire fixes without staging still write weak ingest_binding values."""
        with _patched_modules("putval", "derive", "batch", "skew", "export"):
            assert stage(BATCHES / "001-gauge-basic.txt").returncode == 0
            envelope = json.loads(STAGING.read_text(encoding="utf-8"))
            assert envelope["ingest_binding"].startswith("flushes:")

    def test_partial_staging_export_still_fails_skew_edge(self) -> None:
        """Staging and export fixes without skew still reject inclusive skew edge."""
        export = OUTPUT / "partial-staging-export-skew.json"
        cfg = load_config()
        text = (BATCHES / "005-skew-edge.txt").read_text(encoding="utf-8")
        want = reference_ingest([text], cfg, ["005-skew-edge.txt"])
        with _patched_modules("staging", "export"):
            proc = ingest(BATCHES / "005-skew-edge.txt", export)
            assert_mismatch_or_missing(proc, want, export)

    def test_partial_golden_staging_export_still_reingests_without_pipeline(self) -> None:
        """Golden staging/export without pipeline fix must still re-parse batch files on export."""
        fixture = "001-gauge-basic.txt"
        saved = _snapshot_sources()
        pipeline_path = APP / "internal/pipeline/pipeline.go"
        saved_pipeline = pipeline_path.read_text(encoding="utf-8")
        try:
            shutil.copyfile(BROKEN / "pipeline.go", pipeline_path)
            _restore_broken_sources()
            for name in ("putval", "derive", "batch", "skew", "staging", "export"):
                _install_patch(name)
            build_cli()
            assert stage(BATCHES / fixture).returncode == 0
            envelope = json.loads(STAGING.read_text(encoding="utf-8"))
            tampered = -5151
            envelope["report"]["flushes"][0]["metrics"][0]["value"] = tampered
            envelope["ingest_binding"] = reference_binding(envelope["report"])
            STAGING.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")
            out = OUTPUT / "partial-pipeline-reingest.json"
            proc = export_out(out)
            if proc.returncode != 0 or not out.is_file():
                return
            got = json.loads(out.read_text(encoding="utf-8"))
            if got["flushes"][0]["metrics"][0]["value"] == tampered:
                raise AssertionError("broken pipeline still re-ingested instead of publishing staging")
        finally:
            pipeline_path.write_text(saved_pipeline, encoding="utf-8")
            _restore_sources(saved)
            build_cli()
