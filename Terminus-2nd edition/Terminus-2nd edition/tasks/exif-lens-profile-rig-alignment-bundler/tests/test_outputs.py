"""Behavioral verifier for rigbundle photogrammetry alignment pipeline."""

from __future__ import annotations

import json
import os
import random
import subprocess
from pathlib import Path

import pytest

from reference_bundle import (
    compute_captures_digest,
    load_captures,
    load_checker,
    load_json,
    mount_sha256,
    normalize_exif_ms,
    reference_align,
)

APP = Path("/app")
CLI = Path("/app/bin/rigbundle")
RESET = APP / "scripts/reset-state.sh"
STAGING = APP / "state/capture-staging.json"
STAGING_SEQ = APP / "state/staging-seq.json"
ALIGN_GEN = APP / "state/align-generation.json"
BUNDLE_OUT = APP / "output/bundle-manifest.json"
REJECTED = APP / "output/rejected-captures.jsonl"
EXIF = APP / "fixtures/exif/alpha-captures.jsonl"
MOUNT = APP / "fixtures/inventory/rig-alpha.json"
LENSES = APP / "fixtures/lenses/profiles-east.json"
CHECKER = APP / "fixtures/checkerboard/alpha-board.jsonl"
SEEDS = json.loads((APP / "fixtures/seeds.json").read_text(encoding="utf-8"))["seeds"]
HIDDEN = Path("/opt/verifier-fixtures/rig-delta")
PATCHES = Path(__file__).resolve().parent / "patches"


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged["PATH"] = "/app/bin:/opt/verifier-venv/bin:/usr/local/bin:" + merged.get("PATH", "")
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ingest(exif: Path | None = None, mount: Path | None = None, env: dict | None = None) -> None:
    proc = run(
        ["bash", str(CLI), "ingest", "--exif", str(exif or EXIF), "--mount", str(mount or MOUNT)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def align(lenses: Path | None = None, checker: Path | None = None, env: dict | None = None) -> None:
    proc = run(
        [
            "bash",
            str(CLI),
            "align",
            "--lenses",
            str(lenses or LENSES),
            "--checkerboard",
            str(checker or CHECKER),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def export_bundle() -> None:
    proc = run(["bash", str(CLI), "export"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def pipeline(
    exif: Path | None = None,
    mount: Path | None = None,
    lenses: Path | None = None,
    checker: Path | None = None,
    env: dict | None = None,
) -> None:
    ingest(exif, mount, env)
    align(lenses, checker, env)
    export_bundle()


def test_instruction_output_paths_after_pipeline() -> None:
    """Full pipeline writes every instruction output path under /app/state and /app/output."""
    reset()
    pipeline()
    assert str(STAGING) == "/app/state/capture-staging.json"
    assert str(STAGING_SEQ) == "/app/state/staging-seq.json"
    assert str(ALIGN_GEN) == "/app/state/align-generation.json"
    assert str(BUNDLE_OUT) == "/app/output/bundle-manifest.json"
    assert str(REJECTED) == "/app/output/rejected-captures.jsonl"
    for path in (STAGING, STAGING_SEQ, ALIGN_GEN, BUNDLE_OUT, REJECTED):
        assert path.is_file()


class TestIngestStaging:
    def test_ingest_writes_capture_staging_path(self) -> None:
        """Ingest writes /app/state/capture-staging.json with staged capture rows."""
        reset()
        ingest()
        body = json.loads(STAGING.read_text(encoding="utf-8"))
        assert len(body["captures"]) >= 6

    def test_captures_digest_matches_reference(self) -> None:
        """Staging captures_digest matches independent sha256 canonical line digest."""
        reset()
        ingest()
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        caps = load_captures(EXIF)
        assert snap["captures_digest"] == compute_captures_digest(caps)

    def test_mount_sha256_recorded(self) -> None:
        """Staging records mount_sha256 of the ingested mount inventory bytes."""
        reset()
        ingest()
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert snap["mount_sha256"] == mount_sha256(MOUNT)

    def test_staging_seq_increments(self) -> None:
        """Ingest bumps /app/state/staging-seq.json staging_generation counter."""
        reset()
        ingest()
        assert str(STAGING_SEQ) == "/app/state/staging-seq.json"
        seq = json.loads(STAGING_SEQ.read_text(encoding="utf-8"))
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert seq["staging_generation"] == snap["staging_generation"] >= 1

    def test_rejected_captures_path_after_align(self) -> None:
        """Align writes rejected-captures.jsonl at the instruction output path."""
        reset()
        ingest()
        align()
        assert str(REJECTED) == "/app/output/rejected-captures.jsonl"
        assert REJECTED.is_file()


class TestAlignGeneration:
    def test_align_bumps_generation_file(self) -> None:
        """Align writes /app/state/align-generation.json with generation at least one."""
        reset()
        ingest()
        align()
        gen = json.loads(ALIGN_GEN.read_text(encoding="utf-8"))
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert gen["generation"] >= 1
        assert gen["staging_generation"] == snap["staging_generation"]

    def test_export_fails_after_ingest_without_align(self) -> None:
        """Export rejects align_generation zero before align stage runs."""
        reset()
        ingest()
        proc = run(["bash", str(CLI), "export"])
        assert proc.returncode != 0


class TestDomainRules:
    def test_rig_slot_mismatch_rejected(self) -> None:
        """Wrong camera serial for rig slot lands in rejected-captures.jsonl."""
        reset()
        pipeline()
        lines = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert any(r["capture_id"] == "cap-006" and r["reason"] == "rig_slot_mismatch" for r in lines)

    def test_lens_not_allowed_rejected(self) -> None:
        """Lens outside allowed_lens_ids is rejected with lens_not_allowed."""
        reset()
        pipeline()
        lines = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert any(r["capture_id"] == "cap-005" and r["reason"] == "lens_not_allowed" for r in lines)

    def test_calibration_failed_rejected(self) -> None:
        """Checkerboard failure rejects capture with calibration_failed."""
        reset()
        pipeline()
        lines = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert any(r["capture_id"] == "cap-007" and r["reason"] == "calibration_failed" for r in lines)

    def test_missing_frame_accounting_slot_one(self) -> None:
        """Missing frame index 3 is listed for rig slot 1 in bundle manifest."""
        reset()
        pipeline()
        body = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        missing = {(m["rig_slot"], m["frame_index"]) for m in body["missing_frames"]}
        assert (1, 3) in missing

    def test_exif_timestamp_normalization_ordering(self) -> None:
        """Aligned entries sort by normalized_ms then capture_id."""
        reset()
        pipeline()
        body = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        caps = load_captures(EXIF)
        mount = load_json(MOUNT)
        checker = load_checker(CHECKER)
        expected, _ = reference_align(
            mount,
            caps,
            load_json(LENSES),
            checker,
            align_generation=json.loads(ALIGN_GEN.read_text(encoding="utf-8"))["generation"],
            staging_generation=json.loads(STAGING.read_text(encoding="utf-8"))["staging_generation"],
            mount_sha=mount_sha256(MOUNT),
        )
        got_ids = [e["capture_id"] for e in body["entries"]]
        exp_ids = [e["capture_id"] for e in expected["entries"]]
        assert got_ids == exp_ids

    def test_lens_profile_revision_selection(self) -> None:
        """Later effective_capture_ms selects newer lens profile revision."""
        reset()
        pipeline()
        body = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["capture_id"] == "cap-003")
        assert row["profile_revision"] == "v3"

    def test_normalized_ms_matches_reference(self) -> None:
        """normalized_ms on cap-001 matches reference EXIF normalization."""
        reset()
        pipeline()
        body = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["capture_id"] == "cap-001")
        cap = next(c for c in load_captures(EXIF) if c["capture_id"] == "cap-001")
        assert row["normalized_ms"] == normalize_exif_ms(cap["timestamp_raw"], int(cap["timestamp_tz"]))


class TestExportContract:
    def test_export_manifest_digest_present(self) -> None:
        """Export writes /app/output/bundle-manifest.json with 64-char manifest_digest."""
        reset()
        pipeline()
        assert str(BUNDLE_OUT) == "/app/output/bundle-manifest.json"
        body = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        assert len(body["manifest_digest"]) == 64
        assert body["manifest_digest"] != "pending"

    def test_export_matches_reference_align(self) -> None:
        """Bundle manifest entries and digest match independent reference_align replay."""
        reset()
        pipeline()
        mount = load_json(MOUNT)
        caps = load_captures(EXIF)
        checker = load_checker(CHECKER)
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        gen = json.loads(ALIGN_GEN.read_text(encoding="utf-8"))
        expected, exp_rej = reference_align(
            mount,
            caps,
            load_json(LENSES),
            checker,
            align_generation=gen["generation"],
            staging_generation=snap["staging_generation"],
            mount_sha=snap["mount_sha256"],
        )
        got = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        assert got["entries"] == expected["entries"]
        assert got["missing_frames"] == expected["missing_frames"]
        assert got["manifest_digest"] == expected["manifest_digest"]
        got_rej = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert got_rej == exp_rej

    def test_export_rejects_tampered_staging_digest(self) -> None:
        """Export rejects tampered captures_digest in capture-staging snapshot."""
        reset()
        pipeline()
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        snap["captures_digest"] = "0" * 64
        STAGING.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        proc = run(["bash", str(CLI), "export"])
        assert proc.returncode != 0


class TestRunSubcommand:
    def test_run_executes_full_pipeline(self) -> None:
        """Run subcommand writes instruction output paths after full ingest align export."""
        reset()
        proc = run(
            [
                "bash",
                str(CLI),
                "run",
                "--exif",
                str(EXIF),
                "--mount",
                str(MOUNT),
                "--lenses",
                str(LENSES),
                "--checkerboard",
                str(CHECKER),
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert BUNDLE_OUT.is_file()
        assert ALIGN_GEN.is_file()
        assert REJECTED.is_file()


class TestHiddenTB3:
    def test_hidden_delta_full_frame_range(self) -> None:
        """Hidden delta fixture reports no missing frames when range is complete."""
        reset()
        hidden_exif = HIDDEN / "captures.jsonl"
        hidden_mount = HIDDEN / "inventory.json"
        hidden_lenses = HIDDEN / "lenses.json"
        hidden_checker = HIDDEN / "checkerboard.jsonl"
        assert str(HIDDEN).startswith("/opt/verifier-fixtures")
        pipeline(hidden_exif, hidden_mount, hidden_lenses, hidden_checker, env={"TB3_FIXTURE_DIR": str(HIDDEN)})
        body = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        assert body["missing_frames"] == []
        assert len(body["entries"]) == 2

    def test_hidden_profile_revision_at_effective_ms(self) -> None:
        """Hidden capture at effective_capture_ms boundary selects v5 profile revision."""
        reset()
        hidden_exif = HIDDEN / "captures.jsonl"
        hidden_mount = HIDDEN / "inventory.json"
        hidden_lenses = HIDDEN / "lenses.json"
        hidden_checker = HIDDEN / "checkerboard.jsonl"
        pipeline(hidden_exif, hidden_mount, hidden_lenses, hidden_checker, env={"TB3_FIXTURE_DIR": str(HIDDEN)})
        body = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        row = next(e for e in body["entries"] if e["capture_id"] == "d-201")
        assert row["profile_revision"] == "v5"


class TestDecoyIsolation:
    def test_decoy_edit_does_not_change_bundle(self) -> None:
        """lib/wrap_decoy.sh edits must not change bundle manifest output."""
        reset()
        pipeline()
        before = BUNDLE_OUT.read_text(encoding="utf-8")
        decoy = APP / "lib/wrap/wrap_decoy.sh"
        original = decoy.read_text(encoding="utf-8")
        try:
            decoy.write_text(original + "\n# decoy marker\n", encoding="utf-8")
            reset()
            pipeline()
            after = BUNDLE_OUT.read_text(encoding="utf-8")
            assert before == after
        finally:
            decoy.write_text(original, encoding="utf-8")


@pytest.mark.parametrize("seed", SEEDS)
def test_parametrized_serial_lens_timestamp_reference(seed: int, tmp_path: Path) -> None:
    """Random camera serial, lens id, and timestamp per seed blocks hardcoded alignment."""
    reset()
    rng = random.Random(seed)
    serial = f"CAM-{rng.randint(1000, 9999)}"
    lens = f"LENS-{rng.randint(100, 999)}"
    slot = 9
    mount_doc = {
        "rig_id": f"rig-{seed}",
        "expected_frames_per_slot": 1,
        "frame_index_start": 1,
        "slots": [{"slot": slot, "camera_serial": serial, "allowed_lens_ids": [lens]}],
    }
    lenses_doc = {
        "profiles": [
            {
                "lens_id": lens,
                "focal_mm": round(20 + rng.random() * 10, 2),
                "profile_revision": f"rev-{seed}",
                "effective_capture_ms": 0,
            }
        ]
    }
    tz = -300
    raw = f"2024-07-{10 + seed % 10:02d}T12:00:00"
    cap = {
        "capture_id": f"param-{seed}",
        "camera_serial": serial,
        "lens_id": lens,
        "timestamp_raw": raw,
        "timestamp_tz": tz,
        "frame_index": 1,
        "rig_slot": slot,
    }
    checker_line = {"capture_id": cap["capture_id"], "board_detected": True, "reprojection_error": 0.1}
    mpath = tmp_path / f"mount-{seed}.json"
    lpath = tmp_path / f"lenses-{seed}.json"
    epath = tmp_path / f"exif-{seed}.jsonl"
    cpath = tmp_path / f"checker-{seed}.jsonl"
    mpath.write_text(json.dumps(mount_doc, indent=2), encoding="utf-8")
    lpath.write_text(json.dumps(lenses_doc, indent=2), encoding="utf-8")
    epath.write_text(json.dumps(cap, separators=(",", ":")) + "\n", encoding="utf-8")
    cpath.write_text(json.dumps(checker_line, separators=(",", ":")) + "\n", encoding="utf-8")
    pipeline(epath, mpath, lpath, cpath)
    expected, _ = reference_align(mount_doc, [cap], lenses_doc, {cap["capture_id"]: checker_line})
    got = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
    assert got["entries"][0] == expected["entries"][0]


class TestProtectedDocs:
    def test_contract_docs_present(self) -> None:
        """All instruction-cited contract documents exist under /app/docs/."""
        for name in (
            "cli-surface.md",
            "capture-staging.md",
            "exif-timestamp-normalization.md",
            "lens-profile-matching.md",
            "missing-frame-accounting.md",
            "rig-slot-constraints.md",
            "checkerboard-gate.md",
            "bundle-manifest-export.md",
        ):
            assert (APP / "docs" / name).is_file(), name


class TestPartialPatches:
    def test_golden_staging_digest_patch(self) -> None:
        """Golden staging_io patch restores sha256 captures_digest after broken FNV stub."""
        reset()
        target = APP / "lib/staging/staging_io.sh"
        saved = target.read_text(encoding="utf-8")
        broken = (PATCHES / "broken_staging_io.sh").read_text(encoding="utf-8")
        golden = (PATCHES / "golden_staging_io.sh").read_text(encoding="utf-8")
        try:
            target.write_text(broken, encoding="utf-8")
            ingest()
            snap_bad = json.loads(STAGING.read_text(encoding="utf-8"))
            caps = load_captures(EXIF)
            assert snap_bad["captures_digest"] != compute_captures_digest(caps)
            target.write_text(golden, encoding="utf-8")
            reset()
            ingest()
            snap_good = json.loads(STAGING.read_text(encoding="utf-8"))
            assert snap_good["captures_digest"] == compute_captures_digest(caps)
        finally:
            target.write_text(saved, encoding="utf-8")
