"""Consolidated manifest contract verifier for climate array metadata."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from zarr_refmath import (  # noqa: E402
    compressor_fp,
    expected_slots,
    read_manifests,
    reference_manifest,
    reference_staging,
    span_for,
)

APP_ROOT = Path("/app")
CLI_BIN = APP_ROOT / "bin" / "mdcoll"
BUILD_SCRIPT = APP_ROOT / "environment" / "scripts" / "build_all.sh"
STAGING_PATH = APP_ROOT / "state" / "array_staging.json"
MANIFEST_OUT = APP_ROOT / "output" / "consolidated_manifest.json"
BUNDLED_MANIFESTS = APP_ROOT / "environment" / "fixtures" / "manifests"
BUNDLED_AXES = APP_ROOT / "environment" / "fixtures" / "axes.json"
VERIFIER_FIXTURE_ROOT = Path("/opt/verifier-fixtures/zarr_hidden")


@dataclass
class RunContext:
    manifest_dir: Path
    axes_file: Path


def _resolve_manifest_dir() -> Path:
    override = os.environ.get("TB3_MANIFEST_DIR")
    return Path(override) if override else BUNDLED_MANIFESTS


def _resolve_axes_file() -> Path:
    override = os.environ.get("TB3_AXES_PATH")
    return Path(override) if override else BUNDLED_AXES


def _shell(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


@pytest.fixture(scope="module")
def built_cli() -> Path:
    _shell(["bash", str(BUILD_SCRIPT)])
    assert CLI_BIN.is_file()
    return CLI_BIN


@pytest.fixture
def ctx() -> RunContext:
    return RunContext(manifest_dir=_resolve_manifest_dir(), axes_file=_resolve_axes_file())


@pytest.fixture
def fresh_run(built_cli: Path, ctx: RunContext) -> dict:
    STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    for path in (STAGING_PATH, MANIFEST_OUT):
        if path.exists():
            path.unlink()
    _shell(
        [
            str(built_cli),
            "ingest",
            "--manifest-dir",
            str(ctx.manifest_dir),
            "--axes",
            str(ctx.axes_file),
            "--staging",
            str(STAGING_PATH),
        ]
    )
    _shell(
        [
            str(built_cli),
            "export",
            "--staging",
            str(STAGING_PATH),
            "--out",
            str(MANIFEST_OUT),
        ]
    )
    return json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))


class TestBuildAndPaths:
    def test_release_binary_exists_after_build(self, built_cli: Path) -> None:
        """Release build installs the consolidator binary."""
        assert built_cli.name == "mdcoll"

    def test_ingest_emit_creates_artifact_paths(self, fresh_run: dict) -> None:
        """Ingest and export write staging JSON and consolidated manifest paths."""
        assert STAGING_PATH.is_file()
        assert MANIFEST_OUT.is_file()
        assert fresh_run


class TestManifestEnvelope:
    def test_exported_json_has_version_arrays_totals(self, fresh_run: dict) -> None:
        """Exported manifest exposes version, arrays, and totals sections."""
        assert fresh_run["version"] == 1
        assert "arrays" in fresh_run and "totals" in fresh_run

    def test_export_array_names_lexicographic(self, fresh_run: dict) -> None:
        """Array rows are sorted by name ascending."""
        names = [row["name"] for row in fresh_run["arrays"]]
        assert names == sorted(names)

    def test_array_count_field_matches_vector_length(self, fresh_run: dict) -> None:
        """Totals array_count equals the arrays vector length."""
        assert fresh_run["totals"]["array_count"] == len(fresh_run["arrays"])


class TestStagingSnapshot:
    def test_staging_rows_ordered_by_array_name(self, fresh_run: dict) -> None:
        """Staging snapshot rows are sorted by array_name ascending."""
        staged = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
        names = [row["array_name"] for row in staged]
        assert names == sorted(names)

    def test_staging_payload_matches_reference_rows(self, fresh_run: dict, ctx: RunContext) -> None:
        """Staging rows match independent reference_staging math."""
        staged = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
        ref = reference_staging(ctx.manifest_dir, ctx.axes_file)
        for got, want in zip(staged, ref):
            assert got["present_chunk_count"] == want["present_chunk_count"]
            assert got["missing_chunk_keys"] == want["missing_chunk_keys"]


class TestReferenceParity:
    def test_golden_manifest_equals_reference_pipeline(self, fresh_run: dict, ctx: RunContext) -> None:
        """Consolidated manifest matches reference_manifest totals and rows."""
        ref = reference_manifest(ctx.manifest_dir, ctx.axes_file)
        assert fresh_run["totals"] == ref["totals"]
        for got, want in zip(fresh_run["arrays"], ref["arrays"]):
            assert got["name"] == want["name"]
            assert got["missing_chunks"] == want["missing_chunks"]
            assert got["compressor_fingerprint"] == want["compressor_fingerprint"]

    def test_double_export_produces_identical_bytes(self, built_cli: Path, ctx: RunContext) -> None:
        """Repeated export yields byte-identical consolidated manifest."""
        STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
        for path in (STAGING_PATH, MANIFEST_OUT):
            if path.exists():
                path.unlink()
        _shell(
            [
                str(built_cli),
                "ingest",
                "--manifest-dir",
                str(ctx.manifest_dir),
                "--axes",
                str(ctx.axes_file),
                "--staging",
                str(STAGING_PATH),
            ]
        )
        _shell([str(built_cli), "export", "--staging", str(STAGING_PATH), "--out", str(MANIFEST_OUT)])
        first_bytes = MANIFEST_OUT.read_bytes()
        _shell([str(built_cli), "export", "--staging", str(STAGING_PATH), "--out", str(MANIFEST_OUT)])
        assert first_bytes == MANIFEST_OUT.read_bytes()


class TestPerArrayContracts:
    def test_pressure_array_lists_missing_shard_11(self, fresh_run: dict) -> None:
        """Pressure array reports absent chunk key 1.1."""
        pressure = next(a for a in fresh_run["arrays"] if a["name"] == "pressure")
        assert "1.1" in pressure["missing_chunks"]

    def test_temperature_array_has_zero_gaps(self, fresh_run: dict) -> None:
        """Temperature array has no missing chunk keys."""
        temp = next(a for a in fresh_run["arrays"] if a["name"] == "temperature")
        assert temp["missing_chunks"] == []

    def test_all_arrays_pass_transform_gate(self, fresh_run: dict) -> None:
        """Every array row has transform_ok true for bundled fixtures."""
        assert all(row["transform_ok"] for row in fresh_run["arrays"])

    def test_temperature_codec_digest_matches_ref(self, fresh_run: dict, ctx: RunContext) -> None:
        """Temperature compressor fingerprint matches reference seal."""
        temp = next(a for a in fresh_run["arrays"] if a["name"] == "temperature")
        manifest = next(m for m in read_manifests(ctx.manifest_dir) if m["name"] == "temperature")
        assert temp["compressor_fingerprint"] == compressor_fp(manifest["compressor"])

    def test_temperature_latitude_affine_span(self, fresh_run: dict, ctx: RunContext) -> None:
        """Temperature latitude span matches affine reference span_for."""
        temp = next(a for a in fresh_run["arrays"] if a["name"] == "temperature")
        axes = json.loads(ctx.axes_file.read_text(encoding="utf-8"))["temperature"]
        ref_span = span_for(axes["coordinates"]["lat"])
        got_span = temp["coordinate_span"]["lat"]
        assert abs(got_span[0] - ref_span[0]) < 1e-6
        assert abs(got_span[1] - ref_span[1]) < 1e-6


class TestAggregateTotals:
    def test_aggregate_missing_count_matches_rows(self, fresh_run: dict) -> None:
        """Totals missing_chunks equals sum of per-array missing key counts."""
        summed = sum(len(row["missing_chunks"]) for row in fresh_run["arrays"])
        assert fresh_run["totals"]["missing_chunks"] == summed

    def test_aggregate_expected_slots_from_staging(self, fresh_run: dict) -> None:
        """Totals expected_chunks equals sum of staging expected_chunk_count."""
        staged = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
        assert fresh_run["totals"]["expected_chunks"] == sum(r["expected_chunk_count"] for r in staged)

    def test_pressure_chunk_slot_enumeration(self, ctx: RunContext) -> None:
        """Pressure grid enumerates four chunk slots via reference math."""
        manifest = next(m for m in read_manifests(ctx.manifest_dir) if m["name"] == "pressure")
        assert expected_slots(manifest["shape"], manifest["chunks"]) == 4


class TestCliSurface:
    def test_split_cli_ingest_export_succeeds(self, built_cli: Path, ctx: RunContext) -> None:
        """Separate ingest and export invocations produce a valid manifest."""
        if STAGING_PATH.exists():
            STAGING_PATH.unlink()
        _shell(
            [
                str(built_cli),
                "ingest",
                "--manifest-dir",
                str(ctx.manifest_dir),
                "--axes",
                str(ctx.axes_file),
                "--staging",
                str(STAGING_PATH),
            ]
        )
        _shell([str(built_cli), "export", "--staging", str(STAGING_PATH), "--out", str(MANIFEST_OUT)])
        payload = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        assert payload["totals"]["array_count"] >= 2


class TestHiddenAndDecoy:
    def test_decoy_telemetry_absent_from_json(self, fresh_run: dict) -> None:
        """Telemetry decoy symbols do not appear in manifest JSON."""
        assert "latency_pad" not in MANIFEST_OUT.read_text(encoding="utf-8")

    def test_tb3_hidden_manifest_humidity_gap(self, built_cli: Path) -> None:
        """TB3 manifest dir includes humidity with missing chunk 1.1."""
        hidden_manifests = VERIFIER_FIXTURE_ROOT / "manifests"
        if not hidden_manifests.is_dir():
            pytest.skip("hidden manifest bundle not mounted")
        os.environ["TB3_MANIFEST_DIR"] = str(hidden_manifests)
        try:
            ctx = RunContext(manifest_dir=hidden_manifests, axes_file=_resolve_axes_file())
            STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)
            MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
            for path in (STAGING_PATH, MANIFEST_OUT):
                if path.exists():
                    path.unlink()
            _shell(
                [
                    str(built_cli),
                    "ingest",
                    "--manifest-dir",
                    str(ctx.manifest_dir),
                    "--axes",
                    str(ctx.axes_file),
                    "--staging",
                    str(STAGING_PATH),
                ]
            )
            _shell([str(built_cli), "export", "--staging", str(STAGING_PATH), "--out", str(MANIFEST_OUT)])
            data = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
            ref = reference_manifest(hidden_manifests, ctx.axes_file)
            assert data["totals"]["array_count"] == ref["totals"]["array_count"]
            humidity = next(a for a in data["arrays"] if a["name"] == "humidity")
            assert "1.1" in humidity["missing_chunks"]
        finally:
            os.environ.pop("TB3_MANIFEST_DIR", None)

    def test_tb3_axes_catalog_override_accepted(self, built_cli: Path) -> None:
        """TB3_AXES_PATH selects alternate axes catalog when set."""
        alt_axes = VERIFIER_FIXTURE_ROOT / "axes_alt.json"
        if not alt_axes.is_file():
            pytest.skip("alternate axes catalog not mounted")
        os.environ["TB3_AXES_PATH"] = str(alt_axes)
        try:
            ctx = RunContext(manifest_dir=_resolve_manifest_dir(), axes_file=alt_axes)
            STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)
            MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
            for path in (STAGING_PATH, MANIFEST_OUT):
                if path.exists():
                    path.unlink()
            _shell(
                [
                    str(built_cli),
                    "ingest",
                    "--manifest-dir",
                    str(ctx.manifest_dir),
                    "--axes",
                    str(ctx.axes_file),
                    "--staging",
                    str(STAGING_PATH),
                ]
            )
            _shell([str(built_cli), "export", "--staging", str(STAGING_PATH), "--out", str(MANIFEST_OUT)])
            data = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
            assert data["totals"]["array_count"] >= 1
        finally:
            os.environ.pop("TB3_AXES_PATH", None)
