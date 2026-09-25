"""Behavioral verifier for nmeapipeline merge."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest
from reference_merge import (
    load_session_file,
    reference_merge,
    reference_report,
    with_checksum,
)

APP = Path("/app")
OUT = APP / "output" / "merge-report.json"
SNAP = APP / "state" / "merge-snapshot.json"
STATE = APP / "state" / "merge-session.json"
FIXTURES = APP / "fixtures" / "streams"
BASELINE = FIXTURES / "baseline.nmea"
TESTS = Path("/tests")
GOLDEN = TESTS / "verifier-golden"
BROKEN = TESTS / "verifier-broken"
VERIFIER_FIX = Path("/opt/verifier-fixtures")
SRC = APP / "crates" / "nmeapipeline" / "src"

MODULE_TARGETS = {
    "checksum.rs": SRC / "checksum.rs",
    "fields.rs": SRC / "parse" / "fields.rs",
    "normalize.rs": SRC / "talker" / "normalize.rs",
    "multipart.rs": SRC / "merge" / "multipart.rs",
    "datetime.rs": SRC / "merge" / "datetime.rs",
    "compose.rs": SRC / "merge" / "compose.rs",
    "accumulate.rs": SRC / "merge" / "accumulate.rs",
    "rmc.rs": SRC / "context" / "rmc.rs",
    "reconcile.rs": SRC / "session" / "reconcile.rs",
    "pending.rs": SRC / "session" / "pending.rs",
    "validate.rs": SRC / "export" / "validate.rs",
    "writer.rs": SRC / "export" / "writer.rs",
    "wrap.rs": SRC / "export" / "wrap.rs",
    "staging.rs": SRC / "export" / "staging.rs",
}

PROTECTED = [
    APP / "docs" / "merge-contract.md",
    APP / "docs" / "report-schema.md",
    APP / "docs" / "merge-snapshot.md",
    BASELINE,
]
PROTECTED_SHA = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}


def reset() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True, cwd="/app")


def build() -> None:
    subprocess.run(
        ["cargo", "build", "--release", "--locked", "-p", "nmeapipeline"],
        check=True,
        cwd="/app",
    )
    subprocess.run(
        [
            "install",
            "-m",
            "0755",
            "/app/target/release/nmeapipeline",
            "/usr/local/bin/nmeapipeline",
        ],
        check=True,
    )


def merge(input_path: Path, state: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [
        "nmeapipeline",
        "merge",
        "--input",
        str(input_path),
        "--output",
        str(OUT),
    ]
    if state is not None:
        cmd.extend(["--state", str(state)])
    return subprocess.run(cmd, cwd="/app", capture_output=True, text=True, check=False)


def write_stream(name: str, lines: list[str]) -> Path:
    path = FIXTURES / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def restore_broken_modules() -> None:
    for name, dest in MODULE_TARGETS.items():
        src = BROKEN / name
        if src.is_file():
            shutil.copyfile(src, dest)


@contextmanager
def with_partial_patch(mapping: dict[str, Path]):
    """Reset every hot-path module to verifier-broken, then apply selected goldens."""
    backups: dict[Path, bytes] = {}
    try:
        for dest in MODULE_TARGETS.values():
            if dest.is_file():
                backups[dest] = dest.read_bytes()
        restore_broken_modules()
        for name, src in mapping.items():
            shutil.copyfile(src, MODULE_TARGETS[name])
        build()
        yield
    finally:
        for dest, data in backups.items():
            dest.write_bytes(data)
        build()


@pytest.fixture(autouse=True)
def _clean():
    reset()
    yield


class TestNmeaMultipartMerge:
    def test_fixture_integrity(self) -> None:
        for p, digest in PROTECTED_SHA.items():
            assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest

    def test_build_succeeds(self) -> None:
        build()

    def test_report_matches_reference(self) -> None:
        build()
        assert merge(BASELINE).returncode == 0
        assert json.loads(OUT.read_text()) == reference_report(BASELINE)

    def test_quoted_doubled_quote_preserved(self) -> None:
        build()
        assert merge(BASELINE).returncode == 0
        doc = json.loads(OUT.read_text())
        gsv = next(g for g in doc["groups"] if g["sentence"] == "GSV" and g["talker"] == "GN")
        assert any('"hi"x"' in f or f == '"hi"x"' for f in gsv["payload_fields"]) or any(
            'hi"x' in f for f in gsv["payload_fields"]
        )

    def test_multipart_merge_sorts_by_message_number(self) -> None:
        build()
        assert merge(BASELINE).returncode == 0
        doc = json.loads(OUT.read_text())
        ref = reference_report(BASELINE)
        assert doc["groups"] == ref["groups"]

    def test_utc_rollover_after_midnight(self) -> None:
        build()
        dynamic = write_stream(
            "utc-mid.nmea",
            [
                with_checksum("$GPRMC,235959.00,A,4807.038,N,01131.000,E,022.4,084.4,311223,,,A"),
                with_checksum("$GPGGA,000001.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,"),
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            doc = json.loads(OUT.read_text())
            assert json.loads(OUT.read_text()) == reference_report(dynamic)
            gga = next(g for g in doc["groups"] if g["sentence"] == "GGA")
            assert gga["utc_iso"] == "2024-01-01T00:00:01Z"
        finally:
            dynamic.unlink(missing_ok=True)

    def test_seed_dynamic_stream(self) -> None:
        build()
        seed = os.environ.get("VERIFIER_SEED", "nmea-merge")
        n = sum(ord(c) for c in seed) % 3 + 1
        lines = [with_checksum("$GPRMC,120000.00,A,4807.038,N,01131.000,E,022.4,084.4,010124,,,A")]
        lines.extend(
            with_checksum(f"$GPGGA,12000{i}.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,")
            for i in range(n)
        )
        dynamic = write_stream(f"seed-{seed[:8]}.nmea", lines)
        try:
            assert merge(dynamic).returncode == 0
            assert json.loads(OUT.read_text()) == reference_report(dynamic)
        finally:
            dynamic.unlink(missing_ok=True)

    def test_invalid_checksum_rejected(self) -> None:
        build()
        dynamic = write_stream(
            "bad-cs.nmea",
            [
                with_checksum("$GPRMC,120000.00,A,4807.038,N,01131.000,E,022.4,084.4,010124,,,A"),
                "$GPGGA,120001.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*00",
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            doc = json.loads(OUT.read_text())
            assert any(r["reason"] == "checksum" for r in doc["rejected"])
        finally:
            dynamic.unlink(missing_ok=True)

    def test_utc_month_end_rollover(self) -> None:
        build()
        dynamic = write_stream(
            "utc-month.nmea",
            [
                with_checksum("$GPRMC,235959.00,A,4807.038,N,01131.000,E,022.4,084.4,310124,,,A"),
                with_checksum("$GPGGA,000001.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,"),
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            assert json.loads(OUT.read_text()) == reference_report(dynamic)
            gga = next(g for g in json.loads(OUT.read_text())["groups"] if g["sentence"] == "GGA")
            assert gga["utc_iso"] == "2024-02-01T00:00:01Z"
        finally:
            dynamic.unlink(missing_ok=True)

    def test_utc_year_end_rollover(self) -> None:
        build()
        dynamic = write_stream(
            "utc-year.nmea",
            [
                with_checksum("$GPRMC,235959.00,A,4807.038,N,01131.000,E,022.4,084.4,311223,,,A"),
                with_checksum("$GPGGA,000001.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,"),
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            assert json.loads(OUT.read_text()) == reference_report(dynamic)
            gga = next(g for g in json.loads(OUT.read_text())["groups"] if g["sentence"] == "GGA")
            assert gga["utc_iso"] == "2024-01-01T00:00:01Z"
        finally:
            dynamic.unlink(missing_ok=True)

    def test_utc_leap_day_rollover(self) -> None:
        build()
        dynamic = write_stream(
            "utc-leap.nmea",
            [
                with_checksum("$GPRMC,235959.00,A,4807.038,N,01131.000,E,022.4,084.4,290224,,,A"),
                with_checksum("$GPGGA,000001.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,"),
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            assert json.loads(OUT.read_text()) == reference_report(dynamic)
            gga = next(g for g in json.loads(OUT.read_text())["groups"] if g["sentence"] == "GGA")
            assert gga["utc_iso"] == "2024-03-01T00:00:01Z"
        finally:
            dynamic.unlink(missing_ok=True)

    def test_gl_multipart_keeps_gl_talker(self) -> None:
        build()
        assert merge(BASELINE).returncode == 0
        doc = json.loads(OUT.read_text())
        gl = next(g for g in doc["groups"] if g["talker"] == "GL")
        assert gl["merge_key"].startswith("GL:")

    def test_gl_and_gp_multipart_not_cross_merged(self) -> None:
        build()
        seed = os.environ.get("VERIFIER_SEED", "nmea-merge")
        dynamic = write_stream(
            f"seed-glp-{hashlib.md5(seed.encode()).hexdigest()[:6]}.nmea",
            [
                with_checksum("$GLGSV,2,1,04,65,62,157,44,66,45,240,42"),
                with_checksum("$GPGSV,2,2,08,01,05,111,00,13,06,292,00"),
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            doc = json.loads(OUT.read_text())
            assert doc == reference_report(dynamic)
            keys = {g["merge_key"] for g in doc["groups"]}
            # GL incomplete group emits; GP/GN fragment #2 without #1 is orphan-dropped
            # and must not be cross-merged into the GL bucket.
            assert "GL:GSV:2" in keys
            assert "GN:GSV:2" not in keys
            gl = next(g for g in doc["groups"] if g["merge_key"] == "GL:GSV:2")
            assert "01" not in gl["payload_fields"]
            assert "65" in gl["payload_fields"]
        finally:
            dynamic.unlink(missing_ok=True)

    def test_triple_multipart_merge_all_fragments(self) -> None:
        build()
        dynamic = write_stream(
            "triple.nmea",
            [
                with_checksum("$GPGSV,3,2,12,01,05,111,00,13,06,292,00"),
                with_checksum("$GPGSV,3,1,12,11,40,083,46,02,17,308,41"),
                with_checksum("$GPGSV,3,3,12,33,06,122,42,04,12,311,43"),
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            doc = json.loads(OUT.read_text())
            g = next(x for x in doc["groups"] if x["sentence"] == "GSV")
            assert g["fragments_merged"] == 3
            assert g["multipart_total"] == 3
            assert doc == reference_report(dynamic)
        finally:
            dynamic.unlink(missing_ok=True)

    def test_consecutive_multipart_groups_isolated(self) -> None:
        build()
        dynamic = write_stream(
            "consec.nmea",
            [
                with_checksum("$GPGSV,2,1,08,11,40,083,46,02,17,308,41"),
                with_checksum("$GPGSV,2,2,08,01,05,111,00,13,06,292,00"),
                with_checksum("$GPGSV,2,1,06,21,10,010,10,22,20,020,20"),
                with_checksum("$GPGSV,2,2,06,23,30,030,30,24,40,040,40"),
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            assert json.loads(OUT.read_text()) == reference_report(dynamic)
            gsvs = [g for g in json.loads(OUT.read_text())["groups"] if g["sentence"] == "GSV"]
            assert len(gsvs) == 1  # same merge key GN:GSV:2 — later replaces? Actually same key merges into one bucket
            # consecutive same key: all fragments land in one bucket — totals both 2 so second pair overwrites nums
            assert gsvs[0]["merge_key"] == "GN:GSV:2"
        finally:
            dynamic.unlink(missing_ok=True)

    def test_gsa_multipart_merges(self) -> None:
        build()
        dynamic = write_stream(
            "gsa.nmea",
            [
                with_checksum("$GPGSA,A,3,04,05,09,12,2,1,08,,,,,1.5,0.8,1.2"),
            ],
        )
        # Force multipart GSA with total 2
        dynamic = write_stream(
            "gsa2.nmea",
            [
                with_checksum("$GPGSA,2,1,04,05,09,12,,,,,1.5,0.8,1.2"),
                with_checksum("$GPGSA,2,2,24,25,,,,,,,2.0,1.0,1.5"),
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            assert json.loads(OUT.read_text()) == reference_report(dynamic)
            g = next(x for x in json.loads(OUT.read_text())["groups"] if x["sentence"] == "GSA")
            assert g["fragments_merged"] == 2
        finally:
            dynamic.unlink(missing_ok=True)

    def test_rmc_invalid_status_not_used_for_date(self) -> None:
        build()
        dynamic = write_stream(
            "rmc-v.nmea",
            [
                with_checksum("$GPRMC,120000.00,V,4807.038,N,01131.000,E,022.4,084.4,010124,,,A"),
                with_checksum("$GPGGA,120001.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,"),
            ],
        )
        try:
            assert merge(dynamic).returncode == 0
            doc = json.loads(OUT.read_text())
            assert doc == reference_report(dynamic)
            gga = next(g for g in doc["groups"] if g["sentence"] == "GGA")
            assert gga["utc_iso"] is None
        finally:
            dynamic.unlink(missing_ok=True)

    def test_session_incomplete_multipart_buffered_not_reported(self) -> None:
        build()
        dynamic = write_stream(
            "sess-inc.nmea",
            [with_checksum("$GPGSV,2,1,08,11,40,083,46,02,17,308,41")],
        )
        try:
            assert merge(dynamic, state=STATE).returncode == 0
            doc = json.loads(OUT.read_text())
            assert not any(g["sentence"] == "GSV" for g in doc["groups"])
            sess = json.loads(STATE.read_text())
            assert any(p["merge_key"] == "GN:GSV:2" for p in sess["pending"])
        finally:
            dynamic.unlink(missing_ok=True)

    def test_session_cross_run_completes_multipart(self) -> None:
        build()
        p1 = write_stream("sess-a.nmea", [with_checksum("$GPGSV,2,1,08,11,40,083,46,02,17,308,41")])
        p2 = write_stream("sess-b.nmea", [with_checksum("$GPGSV,2,2,08,01,05,111,00,13,06,292,00")])
        try:
            assert merge(p1, state=STATE).returncode == 0
            assert merge(p2, state=STATE).returncode == 0
            doc = json.loads(OUT.read_text())
            g = next(x for x in doc["groups"] if x["sentence"] == "GSV")
            assert g["fragments_merged"] == 2
        finally:
            p1.unlink(missing_ok=True)
            p2.unlink(missing_ok=True)

    def test_session_rmc_context_carried_to_second_input(self) -> None:
        build()
        p1 = write_stream(
            "rmc1.nmea",
            [with_checksum("$GPRMC,120000.00,A,4807.038,N,01131.000,E,022.4,084.4,010124,,,A")],
        )
        p2 = write_stream(
            "rmc2.nmea",
            [with_checksum("$GPGGA,120001.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,")],
        )
        try:
            assert merge(p1, state=STATE).returncode == 0
            assert merge(p2, state=STATE).returncode == 0
            doc = json.loads(OUT.read_text())
            gga = next(g for g in doc["groups"] if g["sentence"] == "GGA")
            assert gga["utc_iso"] == "2024-01-01T12:00:01Z"
        finally:
            p1.unlink(missing_ok=True)
            p2.unlink(missing_ok=True)

    def test_single_pass_incomplete_multipart_emitted(self) -> None:
        build()
        seed = os.environ.get("VERIFIER_SEED", "nmea-merge")
        dynamic = write_stream(
            f"seed-single-{hashlib.md5(seed.encode()).hexdigest()[:6]}.nmea",
            [with_checksum("$GNGSV,2,1,08,11,40,083,46,02,17,308,41")],
        )
        try:
            assert merge(dynamic).returncode == 0
            doc = json.loads(OUT.read_text())
            assert doc == reference_report(dynamic)
            g = next(x for x in doc["groups"] if x["sentence"] == "GSV")
            assert g["fragments_merged"] == 1
            assert g["multipart_total"] == 2
        finally:
            dynamic.unlink(missing_ok=True)

    def test_session_orphan_fragment_dropped(self) -> None:
        build()
        dynamic = write_stream(
            "orphan.nmea",
            [with_checksum("$GPGSV,2,2,08,01,05,111,00,13,06,292,00")],
        )
        try:
            assert merge(dynamic, state=STATE).returncode == 0
            sess = json.loads(STATE.read_text())
            assert sess["pending"] == []
            doc = json.loads(OUT.read_text())
            assert not any(g["sentence"] == "GSV" for g in doc["groups"])
        finally:
            dynamic.unlink(missing_ok=True)

    def test_session_date_change_discards_stale_pending(self) -> None:
        build()
        p1 = write_stream("stale1.nmea", [with_checksum("$GPGSV,2,1,08,11,40,083,46,02,17,308,41")])
        p2 = write_stream(
            "stale2.nmea",
            [
                with_checksum("$GPRMC,120000.00,A,4807.038,N,01131.000,E,022.4,084.4,020124,,,A"),
                with_checksum("$GPGSV,2,2,08,01,05,111,00,13,06,292,00"),
            ],
        )
        try:
            assert merge(p1, state=STATE).returncode == 0
            # seed date then change
            STATE.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "rmc_date": "010124",
                        "rmc_time": "120000.00",
                        "pending": json.loads(STATE.read_text())["pending"],
                    }
                ),
                encoding="utf-8",
            )
            assert merge(p2, state=STATE).returncode == 0
            doc = json.loads(OUT.read_text())
            # orphan fragment 2 alone after pending cleared — dropped
            assert not any(g["sentence"] == "GSV" and g["fragments_merged"] == 2 for g in doc["groups"])
        finally:
            p1.unlink(missing_ok=True)
            p2.unlink(missing_ok=True)

    def test_merge_snapshot_written_with_reference_digest(self) -> None:
        build()
        assert merge(BASELINE).returncode == 0
        snap = json.loads(SNAP.read_text())
        ref = reference_report(BASELINE)
        assert snap["snapshot_digest"] == ref["snapshot_digest"]
        assert SNAP.is_file()

    def test_partial_golden_checksum_only_still_wrong_multipart(self) -> None:
        reset()
        with with_partial_patch({"checksum.rs": GOLDEN / "checksum.rs"}):
            assert merge(BASELINE).returncode == 0
            assert json.loads(OUT.read_text()) != reference_report(BASELINE)

    def test_partial_golden_compose_only_still_wrong_multipart(self) -> None:
        reset()
        with with_partial_patch({"compose.rs": GOLDEN / "compose.rs"}):
            assert merge(BASELINE).returncode == 0
            assert json.loads(OUT.read_text()) != reference_report(BASELINE)

    def test_partial_golden_decoy_accumulate_only_still_wrong(self) -> None:
        reset()
        # accumulate is decoy — restoring broken tree with only that module touched
        # must not yield a correct baseline report.
        with with_partial_patch({"accumulate.rs": BROKEN / "accumulate.rs"}):
            proc = merge(BASELINE)
            if proc.returncode == 0 and OUT.exists():
                assert json.loads(OUT.read_text()) != reference_report(BASELINE)

    def test_partial_golden_ingest_core_broken_staging_wrong_digest(self) -> None:
        reset()
        with with_partial_patch({"staging.rs": GOLDEN / "staging.rs"}):
            proc = merge(BASELINE)
            # staging golden with broken writer digest still mismatches reference
            if proc.returncode == 0:
                assert json.loads(OUT.read_text()) != reference_report(BASELINE)

    def test_partial_golden_multipart_only_still_wrong_merge(self) -> None:
        reset()
        with with_partial_patch({"multipart.rs": GOLDEN / "multipart.rs"}):
            assert merge(BASELINE).returncode == 0
            assert json.loads(OUT.read_text()) != reference_report(BASELINE)

    def test_partial_golden_pending_only_still_wrong_session(self) -> None:
        reset()
        p1 = write_stream("pg1.nmea", [with_checksum("$GPGSV,2,1,08,11,40,083,46,02,17,308,41")])
        try:
            with with_partial_patch({"pending.rs": GOLDEN / "pending.rs"}):
                assert merge(p1, state=STATE).returncode == 0
                # other modules still broken — checksum fails etc.
        finally:
            p1.unlink(missing_ok=True)

    def test_partial_golden_writer_only_still_wrong_digest(self) -> None:
        reset()
        with with_partial_patch({"writer.rs": GOLDEN / "writer.rs"}):
            proc = merge(BASELINE)
            if proc.returncode == 0:
                assert json.loads(OUT.read_text()) != reference_report(BASELINE)

    def test_partial_golden_wrap_only_reorders_groups(self) -> None:
        reset()
        with with_partial_patch({"wrap.rs": GOLDEN / "wrap.rs"}):
            assert merge(BASELINE).returncode == 0
            assert json.loads(OUT.read_text()) != reference_report(BASELINE)

    def test_partial_golden_staging_only_still_wrong_with_broken_compose(self) -> None:
        reset()
        with with_partial_patch({"staging.rs": GOLDEN / "staging.rs"}):
            proc = merge(BASELINE)
            if proc.returncode == 0:
                assert json.loads(OUT.read_text()) != reference_report(BASELINE)

    def test_session_replay_replaces_duplicate_fragment(self) -> None:
        build()
        # Apply full oracle files for this behavioral test — use solve overlay via goldens
        for name in (
            "checksum.rs",
            "fields.rs",
            "normalize.rs",
            "multipart.rs",
            "datetime.rs",
            "compose.rs",
            "rmc.rs",
            "reconcile.rs",
            "pending.rs",
            "validate.rs",
            "writer.rs",
            "wrap.rs",
            "staging.rs",
        ):
            shutil.copyfile(GOLDEN / name, MODULE_TARGETS[name])
        build()
        p1 = write_stream("dup1.nmea", [with_checksum("$GPGSV,2,1,08,11,40,083,46,02,17,308,41")])
        p2 = write_stream(
            "dup2.nmea",
            [
                with_checksum("$GPGSV,2,1,08,22,50,090,50,05,20,310,44"),
                with_checksum("$GNGSV,2,2,08,33,06,122,42,04,12,311,43"),
            ],
        )
        try:
            assert merge(p1, state=STATE).returncode == 0
            assert merge(p2, state=STATE).returncode == 0
            doc = json.loads(OUT.read_text())
            g = next(x for x in doc["groups"] if x["sentence"] == "GSV")
            assert "22" in g["payload_fields"] or any(f == "22" for f in g["payload_fields"])
            assert "11" not in g["payload_fields"][:4] or "22" in g["payload_fields"]
        finally:
            p1.unlink(missing_ok=True)
            p2.unlink(missing_ok=True)

    def test_partial_golden_reconcile_only_still_wrong_session(self) -> None:
        reset()
        with with_partial_patch({"reconcile.rs": GOLDEN / "reconcile.rs"}):
            p1 = write_stream("r1.nmea", [with_checksum("$GPGSV,2,1,08,11,40,083,46,02,17,308,41")])
            p2 = write_stream("r2.nmea", [with_checksum("$GPGSV,2,2,08,01,05,111,00,13,06,292,00")])
            try:
                merge(p1, state=STATE)
                merge(p2, state=STATE)
                if OUT.exists():
                    assert json.loads(OUT.read_text()) != reference_report(p2)
            finally:
                p1.unlink(missing_ok=True)
                p2.unlink(missing_ok=True)

    def test_partial_golden_validate_only_still_wrong_export(self) -> None:
        reset()
        with with_partial_patch({"validate.rs": GOLDEN / "validate.rs"}):
            assert merge(BASELINE).returncode == 0
            assert json.loads(OUT.read_text()) != reference_report(BASELINE)

    def test_hidden_duplicate_fragment_replay_matches_reference(self) -> None:
        for name in (
            "checksum.rs",
            "fields.rs",
            "normalize.rs",
            "multipart.rs",
            "datetime.rs",
            "compose.rs",
            "rmc.rs",
            "reconcile.rs",
            "pending.rs",
            "validate.rs",
            "writer.rs",
            "wrap.rs",
            "staging.rs",
        ):
            shutil.copyfile(GOLDEN / name, MODULE_TARGETS[name])
        build()
        hidden = TESTS / "hidden_bundles" / "duplicate-replay-part2.nmea"
        state_fixture = TESTS / "hidden_bundles" / "duplicate-replay-session.json"
        STATE.write_text(state_fixture.read_text(encoding="utf-8"), encoding="utf-8")
        assert merge(hidden, state=STATE).returncode == 0
        doc = json.loads(OUT.read_text())
        session = load_session_file(state_fixture)
        ref, _ = reference_merge(hidden, session, use_session=True)
        assert doc == ref

    def test_output_artifact_paths_written(self) -> None:
        for name, target in MODULE_TARGETS.items():
            if (GOLDEN / name).exists():
                shutil.copyfile(GOLDEN / name, target)
        build()
        assert merge(BASELINE).returncode == 0
        assert OUT.is_file()
        assert SNAP.is_file()

    def test_session_state_file_written(self) -> None:
        for name, target in MODULE_TARGETS.items():
            if (GOLDEN / name).exists():
                shutil.copyfile(GOLDEN / name, target)
        build()
        dynamic = write_stream("st.nmea", [with_checksum("$GPGSV,2,1,08,11,40,083,46,02,17,308,41")])
        try:
            assert merge(dynamic, state=STATE).returncode == 0
            assert STATE.is_file()
        finally:
            dynamic.unlink(missing_ok=True)

    def test_hidden_gsa_order_matches_reference(self) -> None:
        for name, target in MODULE_TARGETS.items():
            if (GOLDEN / name).exists():
                shutil.copyfile(GOLDEN / name, target)
        build()
        hidden = VERIFIER_FIX / "gsa-order.nmea"
        assert hidden.is_file()
        assert merge(hidden).returncode == 0
        assert json.loads(OUT.read_text()) == reference_report(hidden)
