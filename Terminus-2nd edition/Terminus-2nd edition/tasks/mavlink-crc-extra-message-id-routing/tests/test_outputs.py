"""Behavioral verifier for mavctl decode/publish CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from reference_replay import (
    reference_export,
    reference_three_pass,
    reference_two_pass,
)

TESTS = Path(__file__).resolve().parent

APP = Path("/app")
CORE = APP / "crates" / "mav-core" / "src"
CLI = "/usr/local/bin/mavctl"
OUTPUT = APP / "output"
STATE = APP / "state"
SNAPSHOT = STATE / "decode.snapshot.json"
FIXTURES = APP / "fixtures"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]
RESET = APP / "scripts" / "reset-state.sh"
BROKEN = Path("/opt/verifier-broken-mavcore")
SOLUTION_PATCHES = Path("/solution/patches")

MSG_GPS_RAW_INT = 24
CORE_SCENARIOS = ["merged-regression"]

MODULES = (
    "parse",
    "validate",
    "seed",
    "session",
    "dedup",
    "checkpoint",
    "route",
    "fact_diff",
    "snapshot",
    "publish",
    "decode",
)

ORACLE_GOLDEN = SOLUTION_PATCHES / "golden_decode.rs"


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
    )


def rebuild_mavctl() -> None:
    for mod in MODULES:
        (CORE / f"{mod}.rs").touch()
    proc = run(
        [
            "bash",
            "-c",
            (
                'export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}" && '
                "cargo build --locked --release --bin mavctl && "
                "install -m 0755 target/release/mavctl /usr/local/bin/mavctl"
            ),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def install_modules(golden_dir: Path, only_broken: set[str]) -> None:
    for mod in MODULES:
        dest = CORE / f"{mod}.rs"
        if mod in only_broken:
            shutil.copy2(BROKEN / f"{mod}.rs", dest)
        else:
            shutil.copy2(golden_dir / f"golden_{mod}.rs", dest)
        dest.touch()


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def stream_path(name: str) -> Path:
    entry = next(item for item in CATALOG["scenarios"] if item["name"] == name)
    return FIXTURES / entry["stream"]


def export_path(scenario: str, seed: str) -> Path:
    return OUTPUT / f"{scenario}-{seed}.json"


def decode_cli(
    scenario: str,
    seed: str,
    *,
    checkpoint: Path | None = None,
    resume: bool = False,
    export_name: str | None = None,
) -> subprocess.CompletedProcess[str]:
    out = OUTPUT / (export_name or f"{scenario}-{seed}.json")
    cmd = [
        CLI,
        "decode",
        "--input",
        str(stream_path(scenario)),
        "--seed",
        seed,
        "--export",
        str(out),
    ]
    if checkpoint is not None:
        cmd.extend(["--checkpoint", str(checkpoint)])
    if resume:
        cmd.append("--resume")
    return run(cmd)


def diff_row_for(
    export: dict,
    sysid: int,
    compid: int,
    msg_id: int,
    fact_key: str,
) -> dict:
    matches = [
        row
        for row in export.get("diff_rows", [])
        if row.get("sysid") == sysid
        and row.get("compid") == compid
        and row.get("msg_id") == msg_id
        and row.get("fact_key") == fact_key
    ]
    assert len(matches) == 1, f"expected one diff row for {fact_key}, got {matches}"
    return matches[0]


@pytest.fixture(scope="session")
def golden_dir() -> Path:
    if ORACLE_GOLDEN.is_file():
        return SOLUTION_PATCHES
    pytest.skip("oracle golden modules not mounted")


@pytest.fixture(autouse=True)
def _reset_env() -> None:
    reset()


def test_resume_session_seeded_from_checkpoint() -> None:
    """Resume must seed seq guards from checkpoint rows before filtering new frames."""
    seed = SEEDS[0]
    cp = STATE / "session-seed.db"
    proc_a = decode_cli(
        "checkpoint-session-a",
        seed,
        checkpoint=cp,
        export_name="session-a.json",
    )
    assert proc_a.returncode == 0, proc_a.stderr or proc_a.stdout
    proc_b = decode_cli(
        "checkpoint-resume-session-trap",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="session-b.json",
    )
    assert proc_b.returncode == 0, proc_b.stderr or proc_b.stdout
    expected = reference_two_pass(
        stream_path("checkpoint-session-a"),
        stream_path("checkpoint-resume-session-trap"),
        seed,
        cp,
    )
    got = json.loads((OUTPUT / "session-b.json").read_text(encoding="utf-8"))
    assert got == expected
    assert got["stale_seq_dropped"] >= 1


def test_merged_regression_seed_dynamic() -> None:
    """Anti-cheat: merged-regression must match reference for a non-primary seed."""
    seed = SEEDS[2]
    expected = reference_export(stream_path("merged-regression"), seed)
    proc = decode_cli("merged-regression", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(export_path("merged-regression", seed).read_text(encoding="utf-8"))
    assert got == expected


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("scenario_name", CORE_SCENARIOS)
def test_core_catalog_decode_matches_reference(scenario_name: str, seed: str) -> None:
    """Core catalog streams must match the independent reference export."""
    expected = reference_export(stream_path(scenario_name), seed)
    proc = decode_cli(scenario_name, seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(export_path(scenario_name, seed).read_text(encoding="utf-8"))
    assert got == expected


def test_length_edge_payload_and_event_crc() -> None:
    """Short payloads and 24-bit msg_id CRC must validate together."""
    seed = SEEDS[0]
    expected = reference_export(stream_path("length-edge"), seed)
    proc = decode_cli("length-edge", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(export_path("length-edge", seed).read_text(encoding="utf-8"))
    assert got == expected


def test_seq_rollback_drop_counts_stale() -> None:
    """Stale seq rollbacks must drop frames without rejecting u8 wrap-forward elsewhere."""
    seed = SEEDS[0]
    expected = reference_export(stream_path("seq-rollback-drop"), seed)
    proc = decode_cli("seq-rollback-drop", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("seq-rollback-drop", seed).read_text(encoding="utf-8"))
    assert got == expected
    assert got["stale_seq_dropped"] >= 1


def test_u8_wrap_forward_not_treated_as_rollback() -> None:
    """Sequence 250,251,0 on one route must all be accepted."""
    seed = SEEDS[1]
    expected = reference_export(stream_path("u8-wrap-forward"), seed)
    proc = decode_cli("u8-wrap-forward", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("u8-wrap-forward", seed).read_text(encoding="utf-8"))
    assert got == expected
    assert got["valid_frame_count"] == 3


def test_dedup_replay_keeps_distinct_compid_rows() -> None:
    """Dedup must key on compid; same sysid/msg_id/seq on different compids stay distinct."""
    seed = SEEDS[0]
    expected = reference_export(stream_path("dedup-replay"), seed)
    proc = decode_cli("dedup-replay", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("dedup-replay", seed).read_text(encoding="utf-8"))
    assert got == expected
    assert got["valid_frame_count"] >= 2


def test_checkpoint_two_pass_resume_export() -> None:
    """Checkpoint resume across two decode passes must merge accepted frames."""
    seed = SEEDS[0]
    cp = STATE / "two-pass.db"
    proc_a = decode_cli(
        "checkpoint-resume-a",
        seed,
        checkpoint=cp,
        export_name="pass-a.json",
    )
    assert proc_a.returncode == 0, proc_a.stderr or proc_a.stdout
    proc_b = decode_cli(
        "checkpoint-resume-b",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="pass-b.json",
    )
    assert proc_b.returncode == 0, proc_b.stderr or proc_b.stdout
    expected = reference_two_pass(
        stream_path("checkpoint-resume-a"),
        stream_path("checkpoint-resume-b"),
        seed,
        cp,
    )
    got = json.loads((OUTPUT / "pass-b.json").read_text(encoding="utf-8"))
    assert got == expected


def test_triple_checkpoint_resume_preserves_gps_order() -> None:
    """Three resume passes must keep checkpoint rows before new rows in gps_fixes."""
    seed = SEEDS[0]
    cp = STATE / "triple-pass.db"
    assert decode_cli(
        "checkpoint-resume-a",
        seed,
        checkpoint=cp,
        export_name="triple-a.json",
    ).returncode == 0
    assert decode_cli(
        "checkpoint-resume-b",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="triple-b.json",
    ).returncode == 0
    proc_c = decode_cli(
        "checkpoint-resume-c",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="triple-c.json",
    )
    assert proc_c.returncode == 0, proc_c.stderr or proc_c.stdout
    expected = reference_three_pass(
        stream_path("checkpoint-resume-a"),
        stream_path("checkpoint-resume-b"),
        stream_path("checkpoint-resume-c"),
        seed,
        cp,
    )
    got = json.loads((OUTPUT / "triple-c.json").read_text(encoding="utf-8"))
    assert got == expected
    assert len(got["gps_fixes"]) == 2
    assert got["gps_fixes"][0]["lat"] == -111
    assert got["gps_fixes"][1]["lat"] == 333000
    assert got["changed_fact_count"] >= 1
    lat_row = diff_row_for(got, 5, 1, MSG_GPS_RAW_INT, "lat")
    assert lat_row["old_value"] == "-111"
    assert lat_row["new_value"] == "333000"
    lon_row = diff_row_for(got, 5, 1, MSG_GPS_RAW_INT, "lon")
    assert lon_row["old_value"] == "222"
    assert lon_row["new_value"] == "-444000"


def test_non_resume_export_has_empty_diff_rows() -> None:
    """First-pass decode must not emit resume fact diffs."""
    seed = SEEDS[0]
    proc = decode_cli("merged-regression", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(export_path("merged-regression", seed).read_text(encoding="utf-8"))
    assert got["changed_fact_count"] == 0
    assert got["diff_rows"] == []


def test_resume_diff_rows_include_stringified_old_and_new_values() -> None:
    """Resume exports must record prior and new decoded facts as JSON scalar strings."""
    seed = SEEDS[0]
    cp = STATE / "diff-scalar.db"
    assert decode_cli(
        "checkpoint-resume-a",
        seed,
        checkpoint=cp,
        export_name="diff-a.json",
    ).returncode == 0
    assert decode_cli(
        "checkpoint-resume-b",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="diff-b.json",
    ).returncode == 0
    proc = decode_cli(
        "checkpoint-resume-c",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="diff-c.json",
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    expected = reference_three_pass(
        stream_path("checkpoint-resume-a"),
        stream_path("checkpoint-resume-b"),
        stream_path("checkpoint-resume-c"),
        seed,
        cp,
    )
    got = json.loads((OUTPUT / "diff-c.json").read_text(encoding="utf-8"))
    assert got == expected
    assert got["changed_fact_count"] == len(expected["diff_rows"])
    for row in got["diff_rows"]:
        assert isinstance(row["old_value"], str), row
        assert isinstance(row["new_value"], str), row
        assert row["old_value"] != row["new_value"], row
    lat_row = diff_row_for(got, 5, 1, MSG_GPS_RAW_INT, "lat")
    assert lat_row["old_value"] == "-111"
    assert lat_row["new_value"] == "333000"
    lon_row = diff_row_for(got, 5, 1, MSG_GPS_RAW_INT, "lon")
    assert lon_row["old_value"] == "222"
    assert lon_row["new_value"] == "-444000"


def test_preamble_noise_resync_decodes_frames() -> None:
    """Leading garbage bytes must be skipped before STX resync."""
    seed = SEEDS[0]
    expected = reference_export(stream_path("preamble-noise"), seed)
    proc = decode_cli("preamble-noise", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(export_path("preamble-noise", seed).read_text(encoding="utf-8"))
    assert got == expected


def test_mixed_invalid_crc_skips_bad_frame() -> None:
    """CRC mismatches must be skipped without aborting the run."""
    seed = SEEDS[1]
    expected = reference_export(stream_path("mixed-invalid-crc"), seed)
    proc = decode_cli("mixed-invalid-crc", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(export_path("mixed-invalid-crc", seed).read_text(encoding="utf-8"))
    assert got == expected


def test_resume_idempotent_second_pass_no_growth() -> None:
    """Re-running resume on the same stream must not duplicate checkpoint rows."""
    seed = SEEDS[1]
    cp = STATE / "idempotent.db"
    decode_cli("checkpoint-resume-b", seed, checkpoint=cp, export_name="first.json")
    decode_cli(
        "checkpoint-resume-b",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="second.json",
    )
    first = json.loads((OUTPUT / "first.json").read_text(encoding="utf-8"))
    second = json.loads((OUTPUT / "second.json").read_text(encoding="utf-8"))
    assert second["valid_frame_count"] == first["valid_frame_count"]
    assert second["routes"] == first["routes"]
    assert second["gps_fixes"] == first["gps_fixes"]
    assert second["events"] == first["events"]
    assert second["checkpoint_frame_count"] == first["valid_frame_count"]
    assert second["deduped_count"] >= 1


def test_signed_gps_lat_lon_are_signed() -> None:
    """GPS_RAW_INT must preserve negative lat/lon from two's-complement payload."""
    seed = SEEDS[1]
    expected = reference_export(stream_path("signed-gps-decode"), seed)
    proc = decode_cli("signed-gps-decode", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("signed-gps-decode", seed).read_text(encoding="utf-8"))
    assert got == expected
    assert any(fix["lat"] < 0 for fix in got["gps_fixes"])
    assert any(fix["lon"] < 0 for fix in got["gps_fixes"])


def test_event_order_by_timestamp() -> None:
    """EVENT_LOG export must be sorted by timestamp_ms, not frame seq."""
    seed = SEEDS[1]
    expected = reference_export(stream_path("event-order"), seed)
    proc = decode_cli("event-order", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("event-order", seed).read_text(encoding="utf-8"))
    assert got == expected
    stamps = [event["timestamp_ms"] for event in got["events"]]
    assert stamps == sorted(stamps)


def test_multi_sysid_route_counts() -> None:
    """Route counts must distinguish sysid/component pairs with independent seq guards."""
    seed = SEEDS[0]
    expected = reference_export(stream_path("multi-msg-routing"), seed)
    proc = decode_cli("multi-msg-routing", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("multi-msg-routing", seed).read_text(encoding="utf-8"))
    assert got == expected
    assert len(got["routes"]) >= 2


def test_reference_independent_of_cli() -> None:
    """Reference replay must compute exports without invoking mavctl."""
    seed = SEEDS[0]
    expected = reference_export(stream_path("merged-regression"), seed)
    assert expected["valid_frame_count"] > 0
    assert expected["routes"]


def test_decode_writes_snapshot_artifact() -> None:
    """Successful decode must persist the decode snapshot before export."""
    seed = SEEDS[0]
    proc = decode_cli("merged-regression", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert SNAPSHOT.is_file(), "decode.snapshot.json missing"
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["seed"] == seed
    assert isinstance(snap["frames"], list)


def test_publish_reads_snapshot_only() -> None:
    """Publish must reflect mutated snapshot bytes, not re-decoded streams."""
    seed = SEEDS[0]
    assert decode_cli("signed-gps-decode", seed).returncode == 0
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["frames"], "snapshot must contain frames"
    frame = snap["frames"][0]
    payload = list(frame["payload"])
    payload[4] = 0
    payload[5] = 0
    payload[6] = 0
    payload[7] = 0
    frame["payload"] = payload
    snap["frames"][0] = frame
    SNAPSHOT.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    publish_out = OUTPUT / "publish-only.json"
    proc = run([CLI, "publish", "--export", str(publish_out)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    published = json.loads(publish_out.read_text(encoding="utf-8"))
    assert published["gps_fixes"][0]["lat"] == 0
    expected = reference_export(stream_path("signed-gps-decode"), seed)
    assert published != expected


def test_publish_without_snapshot_fails() -> None:
    """Publish must fail when no decode snapshot exists."""
    seed = SEEDS[0]
    assert decode_cli("merged-regression", seed).returncode == 0
    SNAPSHOT.unlink(missing_ok=True)
    proc = run([CLI, "publish", "--export", str(OUTPUT / "orphan-publish.json")])
    assert proc.returncode != 0
    assert "snapshot missing" in (proc.stderr or proc.stdout).lower()


def test_contract_output_and_snapshot_paths_after_decode() -> None:
    """Decode must write /app/output/merged-regression-alpha01.json and /app/state/decode.snapshot.json."""
    seed = SEEDS[0]
    proc = decode_cli("merged-regression", seed, export_name="merged-regression-alpha01.json")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (OUTPUT / "merged-regression-alpha01.json").is_file()
    assert SNAPSHOT.is_file()


def test_stream_ingest_extracts_frames_before_validate() -> None:
    """Stream ingest must extract GPS frames before CRC validation on signed-gps-decode."""
    seed = SEEDS[0]
    proc = decode_cli("signed-gps-decode", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(export_path("signed-gps-decode", seed).read_text(encoding="utf-8"))
    assert got["gps_fixes"]


def test_snapshot_payload_stored_as_json_byte_array() -> None:
    """decode.snapshot.json payload must be a JSON byte array per decode-snapshot.md."""
    seed = SEEDS[0]
    proc = decode_cli("signed-gps-decode", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    for frame in snap["frames"]:
        payload = frame["payload"]
        assert isinstance(payload, list), frame
        assert payload, "payload byte array must not be empty"
        assert all(isinstance(b, int) and 0 <= b <= 255 for b in payload), frame


def test_verifier_hidden_dedup_compid_scenario() -> None:
    """Hidden /opt/verifier-fixtures dedup-compid stream must match reference export."""
    fixtures_root = Path("/opt/verifier-fixtures/mavlink")
    hidden_catalog = json.loads((fixtures_root / "catalog.json").read_text(encoding="utf-8"))
    entry = next(s for s in hidden_catalog["scenarios"] if s["name"] == "hidden-dedup-compid")
    stream = fixtures_root / entry["stream"]
    seed = SEEDS[0]
    export_path = OUTPUT / "hidden-dedup-compid.json"
    proc = run(
        [
            CLI,
            "decode",
            "--input",
            str(stream),
            "--seed",
            seed,
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(export_path.read_text(encoding="utf-8"))
    expected = reference_export(stream, seed)
    assert got == expected


def test_verifier_hidden_session_resume_scenario() -> None:
    """Hidden /opt/verifier-fixtures session-resume trap must match two-pass reference."""
    fixtures_root = Path("/opt/verifier-fixtures/mavlink")
    hidden_catalog = json.loads((fixtures_root / "catalog.json").read_text(encoding="utf-8"))
    entry = next(s for s in hidden_catalog["scenarios"] if s["name"] == "hidden-session-resume")
    stream = fixtures_root / entry["stream"]
    seed = SEEDS[0]
    cp = STATE / "hidden-session.db"
    proc_a = run(
        [
            CLI,
            "decode",
            "--input",
            str(stream_path("checkpoint-session-a")),
            "--seed",
            seed,
            "--checkpoint",
            str(cp),
            "--export",
            str(OUTPUT / "hidden-session-a.json"),
        ]
    )
    assert proc_a.returncode == 0, proc_a.stderr or proc_a.stdout
    proc_b = run(
        [
            CLI,
            "decode",
            "--input",
            str(stream),
            "--seed",
            seed,
            "--checkpoint",
            str(cp),
            "--resume",
            "--export",
            str(OUTPUT / "hidden-session-b.json"),
        ]
    )
    assert proc_b.returncode == 0, proc_b.stderr or proc_b.stdout
    expected = reference_two_pass(
        stream_path("checkpoint-session-a"),
        stream,
        seed,
        cp,
    )
    got = json.loads((OUTPUT / "hidden-session-b.json").read_text(encoding="utf-8"))
    assert got == expected


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_validate_fails_crc_catalog(golden_dir: Path) -> None:
    """Golden modules cannot hide wrong crc_extra validation."""
    install_modules(golden_dir, {"validate"})
    rebuild_mavctl()
    seed = SEEDS[0]
    expected = reference_export(stream_path("crc-catalog"), seed)
    proc = decode_cli("crc-catalog", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("crc-catalog", seed).read_text(encoding="utf-8"))
    assert got != expected


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_parse_fails_length_edge(golden_dir: Path) -> None:
    """Golden modules cannot hide truncated payload parsing."""
    install_modules(golden_dir, {"parse"})
    rebuild_mavctl()
    seed = SEEDS[0]
    expected = reference_export(stream_path("length-edge"), seed)
    proc = decode_cli("length-edge", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("length-edge", seed).read_text(encoding="utf-8"))
    assert got != expected


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_seed_fails_event_order(golden_dir: Path) -> None:
    """Golden modules cannot hide seed ordering that breaks EVENT_LOG sort."""
    install_modules(golden_dir, {"seed"})
    rebuild_mavctl()
    seed = SEEDS[1]
    expected = reference_export(stream_path("event-order"), seed)
    proc = decode_cli("event-order", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("event-order", seed).read_text(encoding="utf-8"))
    assert got != expected


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_session_fails_seq_rollback(golden_dir: Path) -> None:
    """Golden modules cannot hide sysid-only session guard rollbacks."""
    install_modules(golden_dir, {"session"})
    rebuild_mavctl()
    seed = SEEDS[0]
    expected = reference_export(stream_path("seq-rollback-drop"), seed)
    proc = decode_cli("seq-rollback-drop", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("seq-rollback-drop", seed).read_text(encoding="utf-8"))
    assert got != expected


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_dedup_fails_compid_trap(golden_dir: Path) -> None:
    """Golden modules cannot hide sysid-only dedup on compid trap streams."""
    install_modules(golden_dir, {"dedup"})
    rebuild_mavctl()
    seed = SEEDS[0]
    expected = reference_export(stream_path("dedup-compid-trap"), seed)
    proc = decode_cli("dedup-compid-trap", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("dedup-compid-trap", seed).read_text(encoding="utf-8"))
    assert got != expected


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_checkpoint_fails_cross_seed_resume(golden_dir: Path) -> None:
    """Golden modules cannot hide cross-seed checkpoint resume contamination."""
    install_modules(golden_dir, {"checkpoint"})
    rebuild_mavctl()
    cp = STATE / "cross-seed.db"
    decode_cli("merged-regression", SEEDS[0], checkpoint=cp, export_name="cross-a.json")
    proc = decode_cli(
        "merged-regression",
        SEEDS[2],
        checkpoint=cp,
        resume=True,
        export_name="cross-b.json",
    )
    assert proc.returncode == 0
    expected = reference_export(stream_path("merged-regression"), SEEDS[2])
    got = json.loads((OUTPUT / "cross-b.json").read_text(encoding="utf-8"))
    assert got != expected


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_fact_diff_fails_old_value(golden_dir: Path) -> None:
    """Golden modules cannot hide null old_value on changed resume facts."""
    install_modules(golden_dir, {"fact_diff"})
    rebuild_mavctl()
    seed = SEEDS[0]
    cp = STATE / "partial-fact-diff.db"
    decode_cli("checkpoint-resume-a", seed, checkpoint=cp, export_name="pfd-a.json")
    decode_cli(
        "checkpoint-resume-b",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="pfd-b.json",
    )
    proc = decode_cli(
        "checkpoint-resume-c",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="pfd-c.json",
    )
    assert proc.returncode == 0
    got = json.loads((OUTPUT / "pfd-c.json").read_text(encoding="utf-8"))
    expected = reference_three_pass(
        stream_path("checkpoint-resume-a"),
        stream_path("checkpoint-resume-b"),
        stream_path("checkpoint-resume-c"),
        seed,
        cp,
    )
    assert got != expected
    lat_row = diff_row_for(got, 5, 1, MSG_GPS_RAW_INT, "lat")
    assert lat_row["old_value"] is None


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_route_fails_signed_gps(golden_dir: Path) -> None:
    """Golden modules cannot hide unsigned GPS decoding."""
    install_modules(golden_dir, {"route"})
    rebuild_mavctl()
    seed = SEEDS[1]
    expected = reference_export(stream_path("signed-gps-decode"), seed)
    proc = decode_cli("signed-gps-decode", seed)
    assert proc.returncode == 0
    got = json.loads(export_path("signed-gps-decode", seed).read_text(encoding="utf-8"))
    assert got != expected


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_publish_fails_checkpoint_merge_order(golden_dir: Path) -> None:
    """Golden modules cannot hide reversed snapshot frame order during publish."""
    install_modules(golden_dir, {"publish"})
    rebuild_mavctl()
    seed = SEEDS[0]
    cp = STATE / "partial-publish.db"
    decode_cli("checkpoint-resume-a", seed, checkpoint=cp, export_name="pp-a.json")
    decode_cli(
        "checkpoint-resume-b",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="pp-b.json",
    )
    proc = decode_cli(
        "checkpoint-resume-c",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="pp-c.json",
    )
    assert proc.returncode == 0
    expected = reference_three_pass(
        stream_path("checkpoint-resume-a"),
        stream_path("checkpoint-resume-b"),
        stream_path("checkpoint-resume-c"),
        seed,
        cp,
    )
    got = json.loads((OUTPUT / "pp-c.json").read_text(encoding="utf-8"))
    assert got != expected
    assert [fix["lat"] for fix in got["gps_fixes"]] != [
        fix["lat"] for fix in expected["gps_fixes"]
    ]

@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_decode_fails_session_resume_trap(golden_dir: Path) -> None:
    """Golden modules cannot hide missing checkpoint session seeding in decode."""
    install_modules(golden_dir, {"decode"})
    rebuild_mavctl()
    seed = SEEDS[0]
    cp = STATE / "partial-decode-session.db"
    decode_cli("checkpoint-session-a", seed, checkpoint=cp, export_name="pds-a.json")
    proc = decode_cli(
        "checkpoint-resume-session-trap",
        seed,
        checkpoint=cp,
        resume=True,
        export_name="pds-b.json",
    )
    assert proc.returncode == 0
    expected = reference_two_pass(
        stream_path("checkpoint-session-a"),
        stream_path("checkpoint-resume-session-trap"),
        seed,
        cp,
    )
    got = json.loads((OUTPUT / "pds-b.json").read_text(encoding="utf-8"))
    assert got != expected


@pytest.mark.skipif(not ORACLE_GOLDEN.is_file(), reason="oracle golden modules not mounted")
def test_partial_broken_decode_fails_triple_checkpoint_order(golden_dir: Path) -> None:
    """Golden modules cannot hide wrong checkpoint/new merge order in decode."""
    for mod in MODULES:
        shutil.copy2(golden_dir / f"golden_{mod}.rs", CORE / f"{mod}.rs")
    rebuild_mavctl()
    target = CORE / "decode.rs"
    saved_decode = target.read_text(encoding="utf-8")
    try:
        shutil.copy2(TESTS / "broken_decode.rs", target)
        rebuild_mavctl()
        seed = SEEDS[0]
        cp = STATE / "partial-decode-order.db"
        decode_cli("checkpoint-resume-a", seed, checkpoint=cp, export_name="pdo-a.json")
        decode_cli(
            "checkpoint-resume-b",
            seed,
            checkpoint=cp,
            resume=True,
            export_name="pdo-b.json",
        )
        proc = decode_cli(
            "checkpoint-resume-c",
            seed,
            checkpoint=cp,
            resume=True,
            export_name="pdo-c.json",
        )
        assert proc.returncode == 0
        expected = reference_three_pass(
            stream_path("checkpoint-resume-a"),
            stream_path("checkpoint-resume-b"),
            stream_path("checkpoint-resume-c"),
            seed,
            cp,
        )
        got = json.loads((OUTPUT / "pdo-c.json").read_text(encoding="utf-8"))
        assert got != expected
        assert got["gps_fixes"][0]["lat"] != expected["gps_fixes"][0]["lat"]
    finally:
        target.write_text(saved_decode, encoding="utf-8")
        rebuild_mavctl()
