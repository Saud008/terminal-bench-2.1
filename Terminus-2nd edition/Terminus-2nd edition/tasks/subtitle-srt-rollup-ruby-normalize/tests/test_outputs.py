"""Scientific-computing verifier for srtctl temporal closure exports and sealed stage artifacts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from reference_d5b4e8fd_subtitle import (
    EXPORT_FORMAT,
    fnv1a64_bytes,
    load_catalog,
    normalize_export,
    procedural_combo_07_srt,
    procedural_rollup_ruby_23_srt,
    seed_offset_ms,
    snapshot_body_digest,
    snapshot_dir,
)

APP = Path("/app")
CLI = "/usr/local/bin/srtctl"
FIX = APP / "fixtures"
OUT = APP / "output"
STATE = APP / "state" / "srtctl"
HIDDEN = Path("/opt/verifier-fixtures/srtctl")
AGENT_USER = "agent"
CATALOG = load_catalog(FIX / "catalog.json")


def _tool_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    merged = os.environ.copy()
    merged["PATH"] = "/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:" + merged.get(
        "PATH", ""
    )
    if extra:
        merged.update(extra)
    return merged


def _as_agent(cmd: list[str]) -> list[str]:
    """Drop to the unprivileged agent UID for CLI runs and workspace resets."""
    return ["runuser", "-u", AGENT_USER, "--", *cmd]


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _as_agent(cmd),
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
        env=_tool_env(env),
    )


def reset_state() -> None:
    proc = run(["bash", "/app/scripts/reset-state.sh"])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _stage_input_for_agent(src: Path) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    """Copy root-only verifier inputs into an agent-readable temp path for CLI use."""
    td = tempfile.TemporaryDirectory(prefix="srtctl-stage-")
    dest = Path(td.name) / src.name
    shutil.copy2(src, dest)
    os.chmod(td.name, 0o755)
    os.chmod(dest, 0o644)
    return td, dest


def normalize(
    input_path: Path,
    seed: str,
    fixture: str,
    export_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    export_path = export_path or OUT / f"{fixture}-{seed}.json"
    return run(
        [
            CLI,
            "normalize",
            "--in",
            str(input_path),
            "--seed",
            seed,
            "--fixture",
            fixture,
            "--export",
            str(export_path),
        ]
    )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _clean_state() -> None:
    reset_state()


def test_td5b4e8_catalog_lists_bundled_fixtures() -> None:
    """Fixture catalog advertises the bundled SRT admission inputs."""
    assert len(CATALOG) >= 7
    assert "baseline" in CATALOG
    assert "rollup-chain" in CATALOG


def test_td5b4e8_baseline_export_schema_closure() -> None:
    """Baseline normalize export carries srt-normalized-v1 schema fields."""
    proc = normalize(FIX / "baseline.srt", "alpha01", "baseline")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_json(OUT / "baseline-alpha01.json")
    assert doc["format"] == EXPORT_FORMAT
    assert doc["fixture"] == "baseline"
    assert doc["seed"] == "alpha01"
    assert "seed_offset_ms" in doc
    assert "cues" in doc and "stats" in doc


def test_td5b4e8_baseline_matches_reference() -> None:
    """Baseline export numerically matches independent reference closure."""
    proc = normalize(FIX / "baseline.srt", "alpha01", "baseline")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / "baseline-alpha01.json")
    ref = normalize_export(FIX / "baseline.srt", "alpha01", "baseline")
    assert got == ref


@pytest.mark.parametrize("seed", ["alpha01", "gamma99", "epoch07"])
def test_td5b4e8_seed_offset_reference_parity(seed: str) -> None:
    """Seed offset chronology shift matches FNV-1a64 reference math."""
    proc = normalize(FIX / "baseline.srt", seed, "baseline")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / f"baseline-{seed}.json")
    assert got["seed_offset_ms"] == seed_offset_ms(seed)


def test_td5b4e8_dot_millis_parse_closure() -> None:
    """Dot-separated fractional seconds parse to the same chronology as comma inputs."""
    proc = normalize(FIX / "dot-millis.srt", "beta17", "dot-millis")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / "dot-millis-beta17.json")
    ref = normalize_export(FIX / "dot-millis.srt", "beta17", "dot-millis")
    assert got == ref
    assert got["stats"]["parsed"] == 2


def test_td5b4e8_overlap_merge_trim_counter() -> None:
    """Overlap trim closure records end-time trims in export stats."""
    proc = normalize(FIX / "overlap-merge.srt", "alpha01", "overlap-merge")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / "overlap-merge-alpha01.json")
    ref = normalize_export(FIX / "overlap-merge.srt", "alpha01", "overlap-merge")
    assert got == ref
    assert got["stats"]["overlap_trims"] >= 1
    assert got["cues"][0]["end_ms"] <= got["cues"][1]["start_ms"]


def test_td5b4e8_ruby_an8_segment_extension() -> None:
    """Ruby segment end extensions respect ruby_shift_ms caps after overlap closure."""
    proc = normalize(FIX / "ruby-an8.srt", "gamma99", "ruby-an8")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / "ruby-an8-gamma99.json")
    ref = normalize_export(FIX / "ruby-an8.srt", "gamma99", "ruby-an8")
    assert got == ref
    assert got["stats"]["ruby_shifts"] >= 1
    seg = got["cues"][0]["ruby_segments"][0]
    assert seg["end_ms"] > seg["start_ms"]


def test_td5b4e8_rollup_chain_space_join() -> None:
    """Roll-up merge joins display text with a single ASCII space between cues."""
    proc = normalize(FIX / "rollup-chain.srt", "delta42", "rollup-chain")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / "rollup-chain-delta42.json")
    ref = normalize_export(FIX / "rollup-chain.srt", "delta42", "rollup-chain")
    assert got == ref
    merged = next(c for c in got["cues"] if c.get("rolled_up"))
    assert " " in merged["text"]
    assert "\n" not in merged["text"]
    assert got["stats"]["rollup_removals"] >= 1


def test_td5b4e8_rollup_chain_sentence_boundary() -> None:
    """Roll-up stops at sentence-ending punctuation on the prior cue."""
    proc = normalize(FIX / "rollup-chain.srt", "delta42", "rollup-chain")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / "rollup-chain-delta42.json")
    assert got["stats"]["exported"] >= 2


def test_td5b4e8_bom_crlf_ingest() -> None:
    """UTF-8 BOM and CRLF fixtures parse into chronology-closed exports."""
    proc = normalize(FIX / "bom-crlf.srt", "alpha01", "bom-crlf")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / "bom-crlf-alpha01.json")
    ref = normalize_export(FIX / "bom-crlf.srt", "alpha01", "bom-crlf")
    assert got == ref


def test_td5b4e8_multiline_arrow_text_preserved() -> None:
    """Multiline cue text containing --> does not split into extra cues."""
    proc = normalize(FIX / "multiline-arrow.srt", "beta17", "multiline-arrow")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / "multiline-arrow-beta17.json")
    ref = normalize_export(FIX / "multiline-arrow.srt", "beta17", "multiline-arrow")
    assert got == ref
    assert got["stats"]["parsed"] == 2
    assert "-->" in got["cues"][0]["text"]


def test_td5b4e8_snapshot_artifact_written() -> None:
    """Stage 1 persists normalize-snapshot.json under the fixture-seed state directory."""
    proc = normalize(FIX / "baseline.srt", "alpha01", "baseline")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = snapshot_dir("baseline", "alpha01") / "normalize-snapshot.json"
    assert snap.is_file()
    payload = load_json(snap)
    assert payload["version"] == 1
    assert payload["fixture"] == "baseline"
    assert payload["seed"] == "alpha01"
    assert payload["parsed_count"] >= 1
    assert isinstance(payload["cues"], list)


def test_td5b4e8_ledger_seals_snapshot_digest() -> None:
    """Ledger snapshot_digest binds to raw snapshot bytes via FNV-1a64."""
    proc = normalize(FIX / "baseline.srt", "alpha01", "baseline")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = snapshot_dir("baseline", "alpha01") / "normalize-snapshot.json"
    ledger = snapshot_dir("baseline", "alpha01") / "normalize-ledger.json"
    assert snap.is_file() and ledger.is_file()
    ledger_doc = load_json(ledger)
    snap_doc = load_json(snap)
    assert ledger_doc["snapshot_digest"] == snapshot_body_digest(snap)
    assert ledger_doc["input_digest"] == snap_doc["input_digest"]


def test_td5b4e8_export_seq_first_run() -> None:
    """First normalize run records export_seq 1 in the sealed ledger."""
    proc = normalize(FIX / "baseline.srt", "alpha01", "baseline")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    ledger = load_json(snapshot_dir("baseline", "alpha01") / "normalize-ledger.json")
    marker = (snapshot_dir("baseline", "alpha01") / "export-seq.marker").read_text(encoding="utf-8").strip()
    assert ledger["export_seq"] == 1
    assert marker == "1"


def test_td5b4e8_export_seq_repeat_bytes_identical() -> None:
    """Repeat normalize emits byte-identical export JSON while export_seq increments."""
    export_path = OUT / "repeat.json"
    proc1 = normalize(FIX / "baseline.srt", "alpha01", "baseline", export_path)
    assert proc1.returncode == 0, proc1.stderr or proc1.stdout
    first_bytes = export_path.read_bytes()
    proc2 = normalize(FIX / "baseline.srt", "alpha01", "baseline", export_path)
    assert proc2.returncode == 0, proc2.stderr or proc2.stdout
    second_bytes = export_path.read_bytes()
    assert first_bytes == second_bytes
    marker = (snapshot_dir("baseline", "alpha01") / "export-seq.marker").read_text(encoding="utf-8").strip()
    assert marker == "2"


def test_td5b4e8_hidden_stage_order_trap() -> None:
    """Hidden stage-order trap requires overlap-before-ruby temporal closure."""
    trap = HIDDEN / "stage-order-trap.srt"
    staged, staged_path = _stage_input_for_agent(trap)
    with staged:
        proc = normalize(staged_path, "alpha01", "tb3-stage-order")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_json(OUT / "tb3-stage-order-alpha01.json")
        ref = normalize_export(trap, "alpha01", "tb3-stage-order")
        assert got == ref
        assert got["stats"]["overlap_trims"] >= 1
        assert got["stats"]["ruby_shifts"] >= 1


def test_td5b4e8_hidden_rollup_ruby_trap() -> None:
    """Hidden roll-up trap preserves ruby segments on space-merged export rows."""
    trap = HIDDEN / "rollup-ruby-trap.srt"
    staged, staged_path = _stage_input_for_agent(trap)
    with staged:
        proc = normalize(staged_path, "beta17", "tb3-rollup-ruby")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_json(OUT / "tb3-rollup-ruby-beta17.json")
        ref = normalize_export(trap, "beta17", "tb3-rollup-ruby")
        assert got == ref
        merged = next(c for c in got["cues"] if c.get("rolled_up"))
        assert len(merged["ruby_segments"]) >= 2
        assert " " in merged["text"]


def test_td5b4e8_hidden_digest_seal_trap() -> None:
    """Hidden digest trap rejects publish paths that skip ledger snapshot sealing."""
    trap = HIDDEN / "digest-seal-trap.srt"
    staged, staged_path = _stage_input_for_agent(trap)
    with staged:
        proc = normalize(staged_path, "gamma99", "tb3-digest-seal")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        snap = snapshot_dir("tb3-digest-seal", "gamma99") / "normalize-snapshot.json"
        ledger = load_json(snapshot_dir("tb3-digest-seal", "gamma99") / "normalize-ledger.json")
        assert ledger["snapshot_digest"] == snapshot_body_digest(snap)


def test_td5b4e8_procedural_srt_combo_07() -> None:
    """Procedural seed srt-combo-07 couples overlap trim and ruby extension in one file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "combo.srt"
        path.write_text(procedural_combo_07_srt(), encoding="utf-8")
        os.chmod(tmp, 0o755)
        os.chmod(path, 0o644)
        proc = normalize(path, "srt-combo-07", "srt-combo-07", OUT / "combo-07.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_json(OUT / "combo-07.json")
        ref = normalize_export(path, "srt-combo-07", "srt-combo-07")
        assert got == ref
        assert got["stats"]["overlap_trims"] >= 1 and got["stats"]["ruby_shifts"] >= 1


def test_td5b4e8_procedural_srt_rollup_ruby_23() -> None:
    """Procedural seed srt-rollup-ruby-23 requires roll-up with ruby segment preservation."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "rollup-ruby.srt"
        path.write_text(procedural_rollup_ruby_23_srt(), encoding="utf-8")
        os.chmod(tmp, 0o755)
        os.chmod(path, 0o644)
        proc = normalize(path, "srt-rollup-ruby-23", "srt-rollup-ruby-23", OUT / "rollup-ruby-23.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_json(OUT / "rollup-ruby-23.json")
        ref = normalize_export(path, "srt-rollup-ruby-23", "srt-rollup-ruby-23")
        assert got == ref
        merged = next(c for c in got["cues"] if c.get("rolled_up"))
        assert len(merged["ruby_segments"]) >= 2


def test_td5b4e8_export_index_one_based() -> None:
    """Export cue index values are 1-based after roll-up closure."""
    proc = normalize(FIX / "baseline.srt", "alpha01", "baseline")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(OUT / "baseline-alpha01.json")
    assert got["cues"][0]["index"] == 1


def test_td5b4e8_input_digest_fnv1a64() -> None:
    """Snapshot input_digest matches lowercase hex FNV-1a64 over raw fixture bytes."""
    proc = normalize(FIX / "baseline.srt", "alpha01", "baseline")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = load_json(snapshot_dir("baseline", "alpha01") / "normalize-snapshot.json")
    expected = f"{fnv1a64_bytes((FIX / 'baseline.srt').read_bytes()):016x}"
    assert snap["input_digest"] == expected


@pytest.mark.parametrize(
    "fixture",
    ["baseline", "dot-millis", "overlap-merge", "ruby-an8", "rollup-chain"],
)
def test_td5b4e8_bundled_exports_match_reference(fixture: str) -> None:
    """Bundled fixture exports match independent reference normalize replay."""
    srt = FIX / f"{fixture}.srt"
    seed = "alpha01"
    export_path = OUT / f"{fixture}-ref.json"
    proc = normalize(srt, seed, fixture, export_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(export_path)
    ref = normalize_export(srt, seed, fixture)
    assert got == ref
