"""Behavioral verifier for modbusctl poll staging drift catalog pipeline."""

from __future__ import annotations

import json
import os
import random
import subprocess
from pathlib import Path

import pytest

from reference_catalog import (
    compute_frames_digest,
    decode_raw,
    effective_for_register,
    load_frames,
    load_manifest,
    manifest_sha256,
    reference_catalog,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/modbusctl")
RESET = APP / "scripts" / "reset-state.sh"
STAGING = APP / "state" / "poll-staging.json"
STAGING_SEQ = APP / "state" / "staging-seq.json"
CATALOG_GEN = APP / "state" / "catalog-generation.json"
DRIFT_OUT = APP / "output" / "drift-catalog.json"
REJECTED = APP / "output" / "rejected-frames.jsonl"
MANIFEST = APP / "fixtures" / "manifests" / "plant-alpha.json"
FRAMES = APP / "fixtures" / "frames" / "alpha-poll.jsonl"
SEEDS = json.loads((APP / "fixtures" / "catalog.json").read_text(encoding="utf-8"))["seeds"]
HIDDEN = Path("/opt/verifier-fixtures/modbus-gamma")
PATCHES = Path(__file__).resolve().parent / "patches"

PATCH_TARGETS = {
    "stage": APP / "internal/ingest/stage.go",
    "wordorder": APP / "internal/decode/wordorder.go",
    "epochs": APP / "internal/scale/epochs.go",
    "skew": APP / "internal/clock/skew.go",
    "suppress": APP / "internal/alarm/suppress.go",
    "override": APP / "internal/manifest/override.go",
    "build": APP / "internal/catalog/build.go",
    "export": APP / "internal/export/catalog.go",
}


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged["PATH"] = "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:" + merged.get("PATH", "")
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ingest(manifest: Path | None = None, frames: Path | None = None, env: dict | None = None) -> None:
    proc = run(
        [
            str(CLI),
            "ingest",
            "--manifest",
            str(manifest or MANIFEST),
            "--frames",
            str(frames or FRAMES),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def catalog() -> None:
    proc = run([str(CLI), "catalog"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def export_catalog() -> None:
    proc = run([str(CLI), "export"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def pipeline(manifest: Path | None = None, frames: Path | None = None, env: dict | None = None) -> None:
    ingest(manifest, frames, env)
    catalog()
    export_catalog()


def test_instruction_output_paths_after_pipeline() -> None:
    """Full pipeline writes every instruction output path under /app/state and /app/output."""
    reset()
    pipeline()
    assert str(STAGING) == "/app/state/poll-staging.json"
    assert str(STAGING_SEQ) == "/app/state/staging-seq.json"
    assert str(CATALOG_GEN) == "/app/state/catalog-generation.json"
    assert str(DRIFT_OUT) == "/app/output/drift-catalog.json"
    assert str(REJECTED) == "/app/output/rejected-frames.jsonl"
    assert STAGING.is_file()
    assert STAGING_SEQ.is_file()
    assert CATALOG_GEN.is_file()
    assert DRIFT_OUT.is_file()
    assert REJECTED.is_file()


class TestIngestStaging:
    def test_ingest_writes_poll_staging_path(self) -> None:
        """Ingest writes /app/state/poll-staging.json with staged frame rows."""
        reset()
        ingest()
        assert str(STAGING) == "/app/state/poll-staging.json"
        assert str(STAGING_SEQ) == "/app/state/staging-seq.json"
        assert STAGING.is_file()
        assert STAGING_SEQ.is_file()
        body = json.loads(STAGING.read_text(encoding="utf-8"))
        assert len(body["frames"]) >= 5

    def test_frames_digest_matches_reference(self) -> None:
        """Staging frames_digest matches independent sha256 canonical line digest."""
        reset()
        ingest()
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        frames = load_frames(FRAMES)
        assert snap["frames_digest"] == compute_frames_digest(frames)

    def test_manifest_sha256_recorded(self) -> None:
        """Staging records manifest_sha256 of the ingested manifest file bytes."""
        reset()
        ingest()
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert snap["manifest_sha256"] == manifest_sha256(MANIFEST)

    def test_staging_seq_increments(self) -> None:
        """Ingest bumps /app/state/staging-seq.json staging_generation counter."""
        reset()
        ingest()
        seq = json.loads(STAGING_SEQ.read_text(encoding="utf-8"))
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert seq["staging_generation"] == snap["staging_generation"] >= 1


class TestCatalogGeneration:
    def test_catalog_bumps_generation_file(self) -> None:
        """Catalog writes /app/state/catalog-generation.json with generation at least one."""
        reset()
        ingest()
        catalog()
        assert str(CATALOG_GEN) == "/app/state/catalog-generation.json"
        gen = json.loads(CATALOG_GEN.read_text(encoding="utf-8"))
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert gen["generation"] >= 1
        assert gen["staging_generation"] == snap["staging_generation"]

    def test_export_fails_after_ingest_without_catalog(self) -> None:
        """Export rejects catalog_generation zero before catalog stage runs."""
        reset()
        ingest()
        proc = run([str(CLI), "export"])
        assert proc.returncode != 0


class TestDomainRules:
    def test_uint16_frame_matches_baseline(self) -> None:
        """Uint16 engineering value matches manifest baseline when drift is within threshold."""
        reset()
        pipeline()
        body = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["frame_id"] == "f-001")
        assert row["engineering"] == pytest.approx(100.0)
        assert row["drift_alarm"] is False

    def test_suppression_window_clears_drift_alarm(self) -> None:
        """Alarm suppression window forces drift_alarm false even when drift exceeds threshold."""
        reset()
        pipeline()
        body = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["frame_id"] == "f-002")
        assert row["suppressed"] is True
        assert row["drift_alarm"] is False
        assert row["drift"] > 5.0

    def test_stale_device_clock_rejected(self) -> None:
        """Stale device clocks are written to /app/output/rejected-frames.jsonl and omitted from catalog."""
        reset()
        pipeline()
        lines = REJECTED.read_text(encoding="utf-8").strip().splitlines()
        reasons = {json.loads(line)["frame_id"]: json.loads(line)["reason"] for line in lines if line}
        assert reasons.get("f-003") == "stale_device_clock"
        body = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        assert all(e["frame_id"] != "f-003" for e in body["entries"])

    def test_scale_epoch_boundary_uses_received_ms(self) -> None:
        """Scale epoch selection uses received_ms boundary per scale-epochs.md."""
        reset()
        pipeline()
        body = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["frame_id"] == "f-004")
        assert row["scale_epoch"] == "epoch-v2"
        assert row["engineering"] == pytest.approx(99.0)

    def test_manifest_word_order_override_int32(self) -> None:
        """Per-register manifest override changes int32 word order decoding."""
        reset()
        pipeline()
        body = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["frame_id"] == "f-005")
        manifest = load_manifest(MANIFEST)
        eff = effective_for_register(manifest, 40003)
        fr = next(f for f in load_frames(FRAMES) if f["frame_id"] == "f-005")
        assert row["raw"] == decode_raw(fr, eff["word_order"])

    def test_scale_epoch_pin_override(self) -> None:
        """Register override scale_epoch pin selects pinned epoch regardless of received_ms."""
        reset()
        pipeline()
        body = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["frame_id"] == "f-007")
        assert row["scale_epoch"] == "epoch-v1"
        assert row["engineering"] == pytest.approx(30.0)

    def test_drift_alarm_when_not_suppressed(self) -> None:
        """Drift above threshold raises drift_alarm when suppression window does not apply."""
        reset()
        pipeline()
        body = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["frame_id"] == "f-006")
        assert row["drift_alarm"] is True
        assert row["suppressed"] is False


class TestExportContract:
    def test_export_catalog_digest_present(self) -> None:
        """Export writes /app/output/drift-catalog.json with 64-char catalog_digest."""
        reset()
        pipeline()
        body = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        assert len(body["catalog_digest"]) == 64

    def test_export_matches_reference_catalog(self) -> None:
        """Drift catalog entries and digest match independent reference_catalog replay."""
        reset()
        pipeline()
        manifest = load_manifest(MANIFEST)
        frames = load_frames(FRAMES)
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        expected, exp_rejected = reference_catalog(
            manifest,
            frames,
            catalog_generation=json.loads(CATALOG_GEN.read_text(encoding="utf-8"))["generation"],
            staging_generation=snap["staging_generation"],
        )
        got = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        assert got["entries"] == expected["entries"]
        assert got["catalog_digest"] == expected["catalog_digest"]
        got_rej = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert got_rej == exp_rejected

    def test_export_rejects_tampered_staging_digest(self) -> None:
        """Export rejects tampered frames_digest in poll-staging snapshot."""
        reset()
        pipeline()
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        snap["frames_digest"] = "0" * 64
        STAGING.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        proc = run([str(CLI), "export"])
        assert proc.returncode != 0


class TestRunSubcommand:
    def test_run_executes_full_pipeline(self) -> None:
        """Run subcommand writes instruction output paths after full ingest catalog export."""
        reset()
        proc = run(
            [
                str(CLI),
                "run",
                "--manifest",
                str(MANIFEST),
                "--frames",
                str(FRAMES),
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert str(DRIFT_OUT) == "/app/output/drift-catalog.json"
        assert str(CATALOG_GEN) == "/app/state/catalog-generation.json"
        assert DRIFT_OUT.is_file()
        assert CATALOG_GEN.is_file()
        assert REJECTED.is_file()
        assert str(REJECTED) == "/app/output/rejected-frames.jsonl"


class TestHiddenTB3:
    def test_hidden_gamma_little_endian_override(self) -> None:
        """Hidden gamma fixture honors little-endian word order override on register 50002."""
        reset()
        hidden_manifest = HIDDEN / "manifest.json"
        hidden_frames = HIDDEN / "frames.jsonl"
        assert str(HIDDEN).startswith("/opt/verifier-fixtures")
        pipeline(hidden_manifest, hidden_frames, env={"TB3_FIXTURE_DIR": str(HIDDEN)})
        body = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["frame_id"] == "g-102")
        manifest = load_manifest(hidden_manifest)
        fr = next(f for f in load_frames(hidden_frames) if f["frame_id"] == "g-102")
        eff = effective_for_register(manifest, 50002)
        assert row["raw"] == decode_raw(fr, eff["word_order"])

    def test_hidden_gamma_stale_clock_reject(self) -> None:
        """Hidden gamma fixture rejects g-103 with stale_device_clock in rejected-frames.jsonl."""
        reset()
        hidden_manifest = HIDDEN / "manifest.json"
        hidden_frames = HIDDEN / "frames.jsonl"
        pipeline(hidden_manifest, hidden_frames, env={"TB3_FIXTURE_DIR": str(HIDDEN)})
        lines = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert any(r["frame_id"] == "g-103" and r["reason"] == "stale_device_clock" for r in lines)


class TestDecoyIsolation:
    def test_decoy_edit_does_not_change_catalog(self) -> None:
        """internal/decode/decoy.go edits must not change drift catalog output."""
        reset()
        pipeline()
        before = DRIFT_OUT.read_text(encoding="utf-8")
        decoy = APP / "internal/decode/decoy.go"
        original = decoy.read_text(encoding="utf-8")
        try:
            decoy.write_text(original + "\n// decoy marker\n", encoding="utf-8")
            run(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/modbusctl"])
            reset()
            pipeline()
            after = DRIFT_OUT.read_text(encoding="utf-8")
            assert before == after
        finally:
            decoy.write_text(original, encoding="utf-8")
            run(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/modbusctl"])


@pytest.mark.parametrize("seed", [11, 23, 37])
def test_parametrized_register_scaling_reference(seed: int, tmp_path: Path) -> None:
    """Mutated register map and scale factor per seed blocks hardcoded engineering values."""
    reset()
    rng = random.Random(seed)
    manifest = load_manifest(MANIFEST)
    reg = 41000 + seed
    factor = round(0.01 + rng.random() * 0.05, 4)
    manifest = json.loads(json.dumps(manifest))
    manifest["baseline"][str(reg)] = rng.uniform(1.0, 50.0)
    manifest["scale_epochs"] = [{"epoch_id": "p", "effective_ms": 0, "factor": factor, "offset": 0.0}]
    manifest["register_overrides"] = {}
    manifest["alarm_suppression"] = []
    raw_word = rng.randint(100, 9000)
    received = 1700000000000 + seed * 1000
    frame = {
        "frame_id": f"param-{seed}",
        "device_id": manifest["device_id"],
        "register": reg,
        "width": "uint16",
        "words": [raw_word],
        "received_ms": received,
        "device_clock_ms": received,
    }
    mpath = tmp_path / f"manifest-{seed}.json"
    fpath = tmp_path / f"frames-{seed}.jsonl"
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    fpath.write_text(json.dumps(frame, separators=(",", ":")) + "\n", encoding="utf-8")
    pipeline(mpath, fpath)
    expected, _ = reference_catalog(manifest, [frame])
    got = json.loads(DRIFT_OUT.read_text(encoding="utf-8"))
    assert got["entries"][0]["engineering"] == pytest.approx(expected["entries"][0]["engineering"])


class TestProtectedDocs:
    def test_contract_docs_present(self) -> None:
        """All instruction-cited contract documents exist under /app/docs/."""
        for name in (
            "cli-surface.md",
            "word-order.md",
            "scale-epochs.md",
            "stale-clock.md",
            "alarm-suppression.md",
            "manifest-overrides.md",
            "poll-staging.md",
            "drift-catalog-export.md",
        ):
            assert (APP / "docs" / name).is_file(), name


class TestPartialPatches:
    def test_golden_stage_patch_restores_digest(self) -> None:
        """Golden stage patch restores sha256 frames_digest after broken FNV digest stub."""
        reset()
        target = PATCH_TARGETS["stage"]
        saved = target.read_text(encoding="utf-8")
        broken = (PATCHES / "broken_stage.go").read_text(encoding="utf-8")
        golden = (PATCHES / "golden_stage.go").read_text(encoding="utf-8")
        try:
            target.write_text(broken, encoding="utf-8")
            run(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/modbusctl"])
            ingest()
            snap_bad = json.loads(STAGING.read_text(encoding="utf-8"))
            frames = load_frames(FRAMES)
            assert snap_bad["frames_digest"] != compute_frames_digest(frames)
            target.write_text(golden, encoding="utf-8")
            run(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/modbusctl"])
            reset()
            ingest()
            snap_good = json.loads(STAGING.read_text(encoding="utf-8"))
            assert snap_good["frames_digest"] == compute_frames_digest(frames)
        finally:
            target.write_text(saved, encoding="utf-8")
            run(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/modbusctl"])
