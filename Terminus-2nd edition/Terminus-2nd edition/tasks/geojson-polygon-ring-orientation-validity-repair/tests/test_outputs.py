"""Behavioral verifier for geojson-fix polygon ring repair CLI."""

from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from reference_geojson import reference_report, repair_binding, snapshot_digest, validate_report

APP = Path("/app")
FIXTURES = APP / "fixtures" / "geojson"
OUT = APP / "output" / "repair-report.json"
RESET = APP / "scripts" / "reset-state.sh"
BROKEN = Path("/opt/verifier-broken-geojson")
BROKEN_FALLBACK = Path(__file__).resolve().parent / "broken_lib"
PATCHES = Path(__file__).resolve().parent / "patches"
HIDDEN = Path(__file__).resolve().parent / "hidden_fixtures"
BUILD_SEED = os.environ.get("VERIFIER_SEED", "geojson-ring-repair-v1")

PATCH_TARGETS = {
    "area": APP / "crates/geojson-core/src/area.rs",
    "close": APP / "crates/geojson-core/src/close.rs",
    "sanitize": APP / "crates/geojson-core/src/sanitize.rs",
    "orient": APP / "crates/geojson-core/src/orient.rs",
    "nest": APP / "crates/geojson-core/src/nest.rs",
    "multi": APP / "crates/geojson-core/src/multi.rs",
    "staging": APP / "crates/geojson-core/src/staging.rs",
    "export": APP / "crates/geojson-core/src/export.rs",
}

REPAIR_RS = APP / "crates/geojson-core/src/repair.rs"

SNAPSHOT_PATH = APP / "state" / "repair-snapshot.json"
LEDGER_PATH = APP / "state" / "repair-ledger.json"

FIXTURE_FILES = sorted(p.name for p in FIXTURES.glob("*.json"))
CATALOG_NAMES = sorted(p.stem for p in FIXTURES.glob("*.json"))
HIDDEN_FILES = sorted(p.name for p in HIDDEN.glob("*.json"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PROTECTED_SHA256 = {name: sha256(FIXTURES / name) for name in FIXTURE_FILES}


def reset() -> None:
    proc = subprocess.run(["bash", str(RESET)], check=True, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def broken_root() -> Path:
    return BROKEN if BROKEN.is_dir() else BROKEN_FALLBACK


def build() -> subprocess.CompletedProcess[str]:
    for path in list(PATCH_TARGETS.values()) + [REPAIR_RS]:
        os.utime(path, None)
    return subprocess.run(
        ["cargo", "build", "--locked", "--release", "-p", "geojson-fix"],
        cwd=APP,
        capture_output=True,
        text=True,
        timeout=600,
    )


def install_binary() -> None:
    subprocess.run(
        [
            "install",
            "-m",
            "0755",
            str(APP / "target/release/geojson-fix"),
            "/usr/local/bin/geojson-fix",
        ],
        check=True,
    )


def repair(input_dir: Path | None = None, output: Path | None = None) -> subprocess.CompletedProcess[str]:
    out = output or OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [
            "geojson-fix",
            "repair",
            "--input",
            str(input_dir or FIXTURES),
            "--output",
            str(out),
        ],
        cwd=APP,
        capture_output=True,
        text=True,
        timeout=120,
    )


def snapshot_sources() -> dict[str, str]:
    out = {name: path.read_text(encoding="utf-8") for name, path in PATCH_TARGETS.items()}
    out["repair"] = REPAIR_RS.read_text(encoding="utf-8")
    return out


def restore_sources(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        if name == "repair":
            REPAIR_RS.write_text(content, encoding="utf-8")
        else:
            PATCH_TARGETS[name].write_text(content, encoding="utf-8")


def restore_broken_sources() -> None:
    root = broken_root()
    for name, dest in PATCH_TARGETS.items():
        shutil.copyfile(root / f"{name}.rs", dest)
        os.utime(dest, None)
    shutil.copyfile(root / "repair.rs", REPAIR_RS)
    os.utime(REPAIR_RS, None)


def install_patch(name: str) -> None:
    dest = PATCH_TARGETS[name]
    shutil.copyfile(PATCHES / f"golden_{name}.rs", dest)
    os.utime(dest, None)


def install_all_module_patches() -> None:
    for name in PATCH_TARGETS:
        install_patch(name)


def install_repair_patch() -> None:
    shutil.copyfile(PATCHES / "golden_repair.rs", REPAIR_RS)
    os.utime(REPAIR_RS, None)


@contextmanager
def patched_module(name: str):
    saved = snapshot_sources()
    try:
        restore_broken_sources()
        install_patch(name)
        proc = build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        install_binary()
        yield
    finally:
        restore_sources(saved)
        proc = build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        install_binary()


def isolated_fixture_dir(name: str, *, root: Path = FIXTURES) -> Path:
    tmp = Path(tempfile.mkdtemp(dir="/tmp"))
    shutil.copy(root / name, tmp / name)
    return tmp


def shift_coordinates(coords: Any, dx: float, dy: float) -> Any:
    if isinstance(coords[0][0], (int, float)):
        return [[p[0] + dx, p[1] + dy] for p in coords]
    return [shift_coordinates(part, dx, dy) for part in coords]


def mutate_fixture_dir(seed_tag: str) -> Path:
    rng = random.Random(f"{BUILD_SEED}:{seed_tag}")
    dx = rng.uniform(-50.0, 50.0)
    dy = rng.uniform(-50.0, 50.0)
    tmp = Path(tempfile.mkdtemp(dir="/tmp"))
    for path in sorted(FIXTURES.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        geom = doc["geometry"]
        geom["coordinates"] = shift_coordinates(geom["coordinates"], dx, dy)
        (tmp / path.name).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return tmp


def signed_area_ring(coords: list[list[float]]) -> float:
    verts = coords[:-1] if len(coords) > 1 and coords[0] == coords[-1] else coords
    total = 0.0
    n = len(verts)
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return total * 0.5


def normalize_numbers(obj: Any) -> Any:
    if isinstance(obj, float) and obj.is_integer():
        return int(obj)
    if isinstance(obj, list):
        return [normalize_numbers(v) for v in obj]
    if isinstance(obj, dict):
        return {k: normalize_numbers(v) for k, v in obj.items()}
    return obj


def reports_equal(got: dict[str, Any], expect: dict[str, Any]) -> bool:
    got_norm = normalize_numbers(got)
    expect_norm = normalize_numbers(expect)
    got_binding = got_norm.pop("repair_binding", "")
    expect_binding = expect_norm.pop("repair_binding", "")
    if got_norm != expect_norm:
        return False
    if got_binding and expect_binding:
        return got_binding == expect_binding
    if got_binding:
        fixtures = got_norm["fixtures"]
        stats = got_norm["stats"]
        return got_binding == repair_binding(fixtures, stats)
    return expect_binding == ""


class TestGeojsonFixRepair:
    """GeoJSON polygon ring orientation and validity repair."""

    @classmethod
    def setup_class(cls) -> None:
        proc = build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        install_binary()

    def setup_method(self) -> None:
        reset()

    def test_fixture_integrity(self) -> None:
        """Public fixture JSON must remain byte-stable."""
        for name, digest in PROTECTED_SHA256.items():
            path = FIXTURES / name
            assert path.is_file(), name
            assert sha256(path) == digest, name

    def test_catalog_fixtures_present(self) -> None:
        """All catalog fixtures from docs must exist."""
        assert CATALOG_NAMES == [
            "clean-square",
            "double-close",
            "duplicate-verts",
            "exterior-cw",
            "hole-outside-order",
            "hole-wrong-wind",
            "multi-hole-nest",
            "multi-two",
        ]

    def test_repair_cli_installed(self) -> None:
        """CLI must be on PATH without runtime installs."""
        proc = subprocess.run(["geojson-fix"], capture_output=True, text=True)
        assert proc.returncode == 2
        assert "repair" in (proc.stdout or proc.stderr)

    @pytest.mark.parametrize("fixture", FIXTURE_FILES)
    def test_single_fixture_matches_reference(self, fixture: str) -> None:
        """Each catalog fixture must repair correctly in isolation."""
        tmp = isolated_fixture_dir(fixture)
        try:
            out = APP / "output" / f"single-{fixture}"
            proc = repair(tmp, out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_report(tmp)
            assert reports_equal(got, expect)
            assert validate_report(got)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_full_tree_matches_reference(self) -> None:
        """Full fixture tree must match the independent reference repair."""
        expect = reference_report(FIXTURES)
        proc = repair()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(OUT.read_text(encoding="utf-8"))
        assert reports_equal(got, expect)
        assert validate_report(got)

    def test_export_schema_invariants(self) -> None:
        """Report must satisfy documented schema fields."""
        proc = repair()
        assert proc.returncode == 0, proc.stderr
        doc = json.loads(OUT.read_text(encoding="utf-8"))
        assert doc["report_version"] == 1
        assert doc["valid"] is True
        assert isinstance(doc["repair_binding"], str) and len(doc["repair_binding"]) == 64
        names = [fx["name"] for fx in doc["fixtures"]]
        assert names == sorted(names)
        stats = doc["stats"]
        for key in (
            "fixtures_read",
            "exterior_reversed",
            "interior_reversed",
            "duplicate_vertices_removed",
            "closing_vertices_normalized",
            "rings_reordered",
            "multipolygon_members",
        ):
            assert isinstance(stats[key], int)
        assert stats["fixtures_read"] == len(FIXTURE_FILES)

    def test_full_tree_stats_match_reference(self) -> None:
        """Cumulative repair stats must match the independent reference counters."""
        repair()
        got = json.loads(OUT.read_text(encoding="utf-8"))["stats"]
        expect = reference_report(FIXTURES)["stats"]
        assert got == expect

    def test_exterior_rings_counter_clockwise(self) -> None:
        """Repaired exterior rings must have positive signed area."""
        repair()
        doc = json.loads(OUT.read_text(encoding="utf-8"))
        for fx in doc["fixtures"]:
            coords = fx["coordinates"]
            if fx["geometry_type"] == "Polygon":
                assert signed_area_ring(coords[0]) > 0
            else:
                for poly in coords:
                    assert signed_area_ring(poly[0]) > 0

    def test_interior_rings_clockwise(self) -> None:
        """Repaired holes must have negative signed area."""
        repair()
        doc = json.loads(OUT.read_text(encoding="utf-8"))
        for fx in doc["fixtures"]:
            coords = fx["coordinates"]
            rings = coords[1:] if fx["geometry_type"] == "Polygon" else []
            if fx["geometry_type"] == "MultiPolygon":
                for poly in coords:
                    rings.extend(poly[1:])
            for hole in rings:
                assert signed_area_ring(hole) < 0

    def test_hole_outside_order_repaired(self) -> None:
        """hole-outside-order must pick the large exterior and nest the hole."""
        tmp = isolated_fixture_dir("hole-outside-order.json")
        try:
            out = APP / "output" / "nest-check.json"
            repair(tmp, out)
            fx = json.loads(out.read_text(encoding="utf-8"))["fixtures"][0]
            exterior = fx["coordinates"][0]
            assert len(exterior) == 5
            assert abs(signed_area_ring(exterior)) > 90
            assert len(fx["coordinates"]) == 2
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_multipolygon_member_order_preserved(self) -> None:
        """multi-two must keep polygon index order after repair."""
        tmp = isolated_fixture_dir("multi-two.json")
        try:
            out = APP / "output" / "multi-order.json"
            repair(tmp, out)
            polys = json.loads(out.read_text(encoding="utf-8"))["fixtures"][0]["coordinates"]
            assert polys[0][0][0] == [0.0, 0.0]
            assert polys[1][0][0] == [10.0, 10.0]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_duplicate_and_close_normalized(self) -> None:
        """duplicate-verts and double-close must emit single closing vertex."""
        for fname in ("duplicate-verts.json", "double-close.json"):
            tmp = isolated_fixture_dir(fname)
            try:
                out = APP / "output" / f"norm-{fname}"
                repair(tmp, out)
                ring = json.loads(out.read_text(encoding="utf-8"))["fixtures"][0]["coordinates"][0]
                assert ring[0] == ring[-1]
                assert ring.count(ring[0]) == 2
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def test_seeded_coordinate_mutation_matches_reference(self) -> None:
        """Anti-cheat: shifted coordinates must repair via reference, not baked JSON."""
        tmp = mutate_fixture_dir("coord-shift")
        try:
            out = APP / "output" / "mutated-report.json"
            proc = repair(tmp, out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_report(tmp)
            assert reports_equal(got, expect)
            assert validate_report(got)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_second_mutation_seed_differs(self) -> None:
        """Different verifier seeds must produce different mutated expectations."""
        tmp_a = mutate_fixture_dir("coord-a")
        tmp_b = mutate_fixture_dir("coord-b")
        try:
            expect_a = reference_report(tmp_a)
            expect_b = reference_report(tmp_b)
            assert expect_a != expect_b
        finally:
            shutil.rmtree(tmp_a, ignore_errors=True)
            shutil.rmtree(tmp_b, ignore_errors=True)

    def test_idempotent_repair(self) -> None:
        """Correct repair output is stable across consecutive runs."""
        first = repair()
        assert first.returncode == 0, first.stderr
        first_json = OUT.read_text(encoding="utf-8")
        assert reports_equal(json.loads(first_json), reference_report(FIXTURES))
        second = repair()
        assert second.returncode == 0, second.stderr
        assert OUT.read_text(encoding="utf-8") == first_json

    def test_repair_writes_snapshot(self) -> None:
        """Repair must persist a staging snapshot before export."""
        proc = repair()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert SNAPSHOT_PATH.is_file()
        snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        assert snapshot["sequence"] >= 1
        assert len(snapshot["fixtures"]) == len(FIXTURE_FILES)

    def test_repair_ledger_head_matches_snapshot(self) -> None:
        """Ledger head must match the staged snapshot digest."""
        repair()
        snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        head = ledger["entries"][-1]
        digest = snapshot_digest(snapshot["fixtures"], snapshot["stats"])
        assert head["sequence"] == snapshot["sequence"]
        assert head["fixture_count"] == len(snapshot["fixtures"])
        assert head["snapshot_digest"] == digest

    def test_report_repair_binding_matches_snapshot(self) -> None:
        """Report repair_binding must match the staged snapshot body."""
        repair()
        report = json.loads(OUT.read_text(encoding="utf-8"))
        snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        assert report["repair_binding"] == repair_binding(snapshot["fixtures"], snapshot["stats"])

    def test_export_reads_snapshot_not_arguments(self) -> None:
        """Export must publish snapshot fixtures even if repair passes reversed order."""
        repair()
        snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        report = json.loads(OUT.read_text(encoding="utf-8"))
        assert report["fixtures"] == snapshot["fixtures"]
        assert [fx["name"] for fx in report["fixtures"]] == sorted(fx["name"] for fx in snapshot["fixtures"])

    def test_hidden_fixtures_present(self) -> None:
        """Verifier-only hidden fixtures must ship with the task."""
        assert HIDDEN.is_dir()
        assert HIDDEN_FILES == ["outside-hole-drop.json"]

    @pytest.mark.parametrize("fixture", HIDDEN_FILES)
    def test_hidden_fixture_matches_reference(self, fixture: str) -> None:
        """Hidden fixtures must repair via the independent reference, not bundled shortcuts."""
        tmp = isolated_fixture_dir(fixture, root=HIDDEN)
        try:
            out = APP / "output" / f"hidden-{fixture}"
            proc = repair(tmp, out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_report(tmp)
            assert reports_equal(got, expect)
            assert validate_report(got)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_hidden_outside_hole_dropped(self) -> None:
        """Hidden outside-hole-drop must discard exterior holes."""
        tmp = isolated_fixture_dir("outside-hole-drop.json", root=HIDDEN)
        try:
            out = APP / "output" / "hidden-outside-hole.json"
            repair(tmp, out)
            fx = json.loads(out.read_text(encoding="utf-8"))["fixtures"][0]
            assert len(fx["coordinates"]) == 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_orchestration_nest_before_orient(self) -> None:
        """hole-outside-order exterior must be CCW after nest-then-orient orchestration."""
        tmp = isolated_fixture_dir("hole-outside-order.json")
        try:
            out = APP / "output" / "orchestration-check.json"
            repair(tmp, out)
            fx = json.loads(out.read_text(encoding="utf-8"))["fixtures"][0]
            assert signed_area_ring(fx["coordinates"][0]) > 0
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_all_module_patches_without_repair_still_fails(self) -> None:
        """Golden module patches alone must not pass while repair orchestration stays broken."""
        saved = snapshot_sources()
        repair_saved = REPAIR_RS.read_text(encoding="utf-8")
        try:
            restore_broken_sources()
            install_all_module_patches()
            build_proc = build()
            assert build_proc.returncode == 0, build_proc.stderr or build_proc.stdout
            install_binary()
            proc = repair()
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(OUT.read_text(encoding="utf-8"))
            expect = reference_report(FIXTURES)
            assert not reports_equal(got, expect) or not validate_report(got)
        finally:
            restore_sources(saved)
            REPAIR_RS.write_text(repair_saved, encoding="utf-8")
            build_proc = build()
            assert build_proc.returncode == 0, build_proc.stderr or build_proc.stdout
            install_binary()

    def test_close_stats_append_trap_without_full_repair(self) -> None:
        """Close pass must not count appending a missing closing vertex in stats."""
        saved = snapshot_sources()
        repair_saved = REPAIR_RS.read_text(encoding="utf-8")
        try:
            restore_broken_sources()
            install_all_module_patches()
            close_path = APP / "crates/geojson-core/src/close.rs"
            close_src = close_path.read_text(encoding="utf-8")
            close_src = close_src.replace(
                "            out.push(first);\n        }",
                "            out.push(first);\n            normalized += 1;\n        }",
                1,
            )
            close_path.write_text(close_src, encoding="utf-8")
            build_proc = build()
            assert build_proc.returncode == 0, build_proc.stderr or build_proc.stdout
            install_binary()
            proc = repair()
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(OUT.read_text(encoding="utf-8"))
            expect = reference_report(FIXTURES)
            assert got["stats"] != expect["stats"]
        finally:
            restore_sources(saved)
            REPAIR_RS.write_text(repair_saved, encoding="utf-8")
            build_proc = build()
            assert build_proc.returncode == 0, build_proc.stderr or build_proc.stdout
            install_binary()

    @pytest.mark.parametrize(
        "module",
        ["area", "close", "sanitize", "orient", "nest", "multi", "staging", "export"],
    )
    def test_partial_fix_still_fails_full_tree(self, module: str) -> None:
        """Fixing only one module must not satisfy the full catalog repair."""
        saved = snapshot_sources()
        try:
            restore_broken_sources()
            install_patch(module)
            build_proc = build()
            if build_proc.returncode != 0:
                return
            install_binary()
            proc = repair()
            if proc.returncode != 0:
                return
            got = json.loads(OUT.read_text(encoding="utf-8"))
            expect = reference_report(FIXTURES)
            assert not reports_equal(got, expect) or not validate_report(got)
        finally:
            restore_sources(saved)
            build_proc = build()
            assert build_proc.returncode == 0, build_proc.stderr or build_proc.stdout
            install_binary()
