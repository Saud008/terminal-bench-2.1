"""Behavioral verifier for kh-normalize known_hosts normalization."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_normalize import (
    build_seed_input,
    count_parsed_records,
    load_config,
    manifest_for_run,
    normalize_file,
    normalize_text,
)

APP = Path("/app")
INPUT_DIR = APP / "fixtures" / "inputs"
CONFIG = APP / "config" / "normalize.json"
OUTPUT = APP / "output" / "normalized.hosts"
LEDGER = APP / "state" / "kh-ledger.jsonl"
MANIFEST = APP / "state" / "kh-manifest.json"
CLI = APP / "bin" / "kh-normalize"
SEED = os.environ.get("VERIFIER_SEED", "bash-ssh-known-hosts-hashed-canonicalizer")
TB3_ROOT = Path("/opt/verifier-fixtures/known-hosts")

FIXTURES = sorted(INPUT_DIR.glob("*.hosts"))


def _run(cmd: list[str], *, env: dict | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=merged,
        cwd=str(APP),
    )


def reset_state() -> None:
    proc = _run(["bash", str(APP / "scripts" / "reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def run_normalize(input_path: Path, output: Path = OUTPUT) -> subprocess.CompletedProcess:
    return _run(
        [
            str(CLI),
            "--input",
            str(input_path),
            "--config",
            str(CONFIG),
            "--output",
            str(output),
        ]
    )


class TestNormalizerAntiCheat:
    """CLI-only checks that block shallow or hardcoded fixes."""

    def setup_method(self) -> None:
        reset_state()

    def test_non_catalog_mixed_plain_hashed_matches_reference(self) -> None:
        """Non-catalog mixed plain and hashed input must match the reference normalizer."""
        cfg = load_config(CONFIG)
        text = (
            "Zzz-Plain.Host ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7plain\n"
            "|1|AaBbCcDdEeFf|XxYyZzWwQqRr ssh-ed25519 AAAAC3NzaC1lZDI1NTE5plain\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "mixed-temp.hosts"
            input_path.write_text(text, encoding="utf-8")
            expected = normalize_text(text, cfg)
            proc = run_normalize(input_path)
            assert proc.returncode == 0, proc.stderr
            assert OUTPUT.read_text(encoding="utf-8") == expected

    def test_hashed_salt_case_matches_input(self) -> None:
        """002 hashed salt segments must stay case-sensitive relative to input bytes."""
        fixture = INPUT_DIR / "002-hashed.hosts"
        raw = fixture.read_text(encoding="utf-8")
        salts = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            host = line.split()[0]
            if host.startswith("|1|"):
                parts = host.split("|")
                if len(parts) >= 4:
                    salts.append(parts[2])
        proc = run_normalize(fixture)
        assert proc.returncode == 0, proc.stderr
        out = OUTPUT.read_text(encoding="utf-8")
        for salt in salts:
            assert salt in out

    def test_catalog_and_seed_outputs_differ(self) -> None:
        """Anti-hardcode: seeded input must not match any bundled fixture output."""
        cfg = load_config(CONFIG)
        seed_text = build_seed_input(SEED)
        with tempfile.TemporaryDirectory() as tmp:
            seed_path = Path(tmp) / "seed.hosts"
            seed_path.write_text(seed_text, encoding="utf-8")
            proc = run_normalize(seed_path)
            assert proc.returncode == 0, proc.stderr
            seed_out = OUTPUT.read_text(encoding="utf-8")
            assert seed_out == normalize_text(seed_text, cfg)
            for fixture in FIXTURES:
                assert seed_out != normalize_file(fixture, cfg)


class TestKnownHostsNormalizer:
    """Verifier tests for kh-normalize."""

    def setup_method(self) -> None:
        reset_state()

    @pytest.mark.parametrize("fixture_path", FIXTURES, ids=lambda p: p.name)
    def test_fixture_matches_reference(self, fixture_path: Path) -> None:
        """Catalog fixtures must match the independent reference normalizer."""
        cfg = load_config(CONFIG)
        expected = normalize_file(fixture_path, cfg)
        proc = run_normalize(fixture_path)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        got = OUTPUT.read_text(encoding="utf-8")
        assert got == expected

    def test_missing_input_exits_nonzero(self) -> None:
        """Missing --input must exit 1 and leave normalized output empty."""
        reset_state()
        proc = run_normalize(APP / "fixtures" / "inputs" / "missing.hosts")
        assert proc.returncode == 1
        assert OUTPUT.read_text(encoding="utf-8") == ""

    def test_rerun_is_deterministic(self) -> None:
        """Repeated runs on the same fixture must produce identical bytes."""
        fixture = INPUT_DIR / "006-mixed.hosts"
        proc1 = run_normalize(fixture)
        first = OUTPUT.read_bytes()
        proc2 = run_normalize(fixture)
        second = OUTPUT.read_bytes()
        assert proc1.returncode == 0 and proc2.returncode == 0
        assert first == second

    def test_seed_anti_hardcoding(self) -> None:
        """Seeded bracket/revoked/hashed lines must match reference output."""
        cfg = load_config(CONFIG)
        seed_text = build_seed_input(SEED)
        with tempfile.TemporaryDirectory() as tmp:
            seed_path = Path(tmp) / "seed.hosts"
            seed_path.write_text(seed_text, encoding="utf-8")
            expected = normalize_text(seed_text, cfg)
            proc = run_normalize(seed_path)
            assert proc.returncode == 0, proc.stderr
            got = OUTPUT.read_text(encoding="utf-8")
            assert got == expected
            assert "[seed-" in got and "]:4" in got
            assert not any(line.startswith("@revoked") for line in got.splitlines())
            digest = hashlib.sha256(got.encode("utf-8")).hexdigest()
            assert digest != hashlib.sha256(seed_text.encode("utf-8")).hexdigest()

    def test_003_prefers_non_revoked_duplicate(self) -> None:
        """003 must emit the non-revoked duplicate without @revoked marker."""
        fixture = INPUT_DIR / "003-revoked.hosts"
        proc = run_normalize(fixture)
        assert proc.returncode == 0
        lines = OUTPUT.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert not lines[0].startswith("@revoked")
        assert "active-line" in lines[0]

    def test_004_bracket_port_shape(self) -> None:
        """004 must preserve bracket syntax with lowercased hostnames."""
        fixture = INPUT_DIR / "004-port-bracket.hosts"
        proc = run_normalize(fixture)
        assert proc.returncode == 0
        line = OUTPUT.read_text(encoding="utf-8").splitlines()[0]
        assert "[fallback.local]:2222,[jump.host]:2222" in line

    def test_005_comment_tiebreak(self) -> None:
        """005 duplicate merge must keep lexicographically greatest comment."""
        fixture = INPUT_DIR / "005-duplicates.hosts"
        proc = run_normalize(fixture)
        assert proc.returncode == 0
        line = OUTPUT.read_text(encoding="utf-8").splitlines()[0]
        assert "second comment wins" in line

    def test_006_cert_authority_marker_preserved(self) -> None:
        """006 must retain @cert-authority on surviving normalized lines."""
        fixture = INPUT_DIR / "006-mixed.hosts"
        proc = run_normalize(fixture)
        assert proc.returncode == 0
        lines = OUTPUT.read_text(encoding="utf-8").splitlines()
        cert_lines = [line for line in lines if "@cert-authority" in line]
        assert len(cert_lines) == 1
        assert "ca.example" in cert_lines[0]

    def test_ledger_manifest_matches_input(self) -> None:
        """Parse ledger manifest must bind to raw input bytes after export."""
        fixture = INPUT_DIR / "006-mixed.hosts"
        proc = run_normalize(fixture)
        assert proc.returncode == 0, proc.stderr
        assert MANIFEST.is_file()
        got = json.loads(MANIFEST.read_text(encoding="utf-8"))
        expected = manifest_for_run(fixture, LEDGER)
        assert got == expected

    def test_ledger_record_count_matches_parsed_lines(self) -> None:
        """Ledger line count must equal successfully parsed input records."""
        fixture = INPUT_DIR / "005-duplicates.hosts"
        raw = fixture.read_text(encoding="utf-8")
        proc = run_normalize(fixture)
        assert proc.returncode == 0
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["record_count"] == count_parsed_records(raw)

    def test_staging_ledger_snapshot_after_ingest(self) -> None:
        """Ingest staging must write JSONL ledger rows before export emits output."""
        fixture = INPUT_DIR / "004-port-bracket.hosts"
        proc = run_normalize(fixture)
        assert proc.returncode == 0, proc.stderr
        assert LEDGER.is_file(), "ingest must materialize staging ledger snapshot"
        rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(rows) >= 1
        assert rows[0]["seq"] == 1
        assert "record" in rows[0]

    def test_plain_records_precede_hashed_in_mixed(self) -> None:
        """006 output must list all plain host lines before hashed lines."""
        fixture = INPUT_DIR / "006-mixed.hosts"
        proc = run_normalize(fixture)
        assert proc.returncode == 0
        lines = OUTPUT.read_text(encoding="utf-8").splitlines()
        seen_hashed = False
        for line in lines:
            parts = line.split()
            host = parts[1] if parts[0] in ("@revoked", "@cert-authority") else parts[0]
            if host.startswith("|"):
                seen_hashed = True
            elif seen_hashed:
                pytest.fail("plain host line appeared after hashed record")

    def test_second_run_refreshes_manifest(self) -> None:
        """A second normalize run must re-seal manifest for the new input."""
        first = INPUT_DIR / "001-basic.hosts"
        second = INPUT_DIR / "002-hashed.hosts"
        proc1 = run_normalize(first)
        assert proc1.returncode == 0
        manifest1 = json.loads(MANIFEST.read_text(encoding="utf-8"))
        proc2 = run_normalize(second)
        assert proc2.returncode == 0
        manifest2 = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest2 != manifest1
        assert manifest2 == manifest_for_run(second, LEDGER)

    def test_ledger_seq_starts_at_one(self) -> None:
        """Each ledger JSONL line must carry a monotonic seq starting at 1."""
        fixture = INPUT_DIR / "006-mixed.hosts"
        proc = run_normalize(fixture)
        assert proc.returncode == 0, proc.stderr
        assert LEDGER.is_file()
        seqs: list[int] = []
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            seqs.append(int(obj["seq"]))
        assert seqs == list(range(1, len(seqs) + 1))


@pytest.mark.skipif(not TB3_ROOT.is_dir(), reason="hidden fixtures only in image")
class TestKnownHostsHiddenTraps:
    """Hidden verifier fixtures — independent failure modes from catalog inputs."""

    def setup_method(self) -> None:
        reset_state()

    def test_tb3_bracket_order_matches_reference(self) -> None:
        """Bracket host_sort_key must strip brackets; wrong token sort fails here."""
        fixture = TB3_ROOT / "tb3-bracket-order.hosts"
        assert fixture.is_file(), "TB3 bracket fixture missing"
        cfg = load_config(CONFIG)
        expected = normalize_file(fixture, cfg)
        proc = run_normalize(fixture)
        assert proc.returncode == 0, proc.stderr
        got = OUTPUT.read_text(encoding="utf-8")
        assert got == expected
        lines = got.splitlines()
        assert lines[0].startswith("[apple.box]:9022")
        assert "host.zulu" in lines[1]
        assert lines[2].startswith("[zebra.box]:9022")

    def test_tb3_no_merge_config_emits_both_rows(self) -> None:
        """Hidden merge_duplicates=false config must emit duplicate keys separately."""
        fixture = TB3_ROOT / "tb3-no-merge.hosts"
        hidden_cfg = TB3_ROOT / "tb3-no-merge.json"
        assert fixture.is_file() and hidden_cfg.is_file()
        cfg = load_config(hidden_cfg)
        expected = normalize_file(fixture, cfg)
        proc = _run(
            [
                str(CLI),
                "--input",
                str(fixture),
                "--config",
                str(hidden_cfg),
                "--output",
                str(OUTPUT),
            ]
        )
        assert proc.returncode == 0, proc.stderr
        got = OUTPUT.read_text(encoding="utf-8")
        assert got == expected
        assert got.count("alpha.hidden") == 2

    def test_tb3_hashed_comment_preserved_on_export(self) -> None:
        """Export stage must preserve hashed-line comments (emit-layer trap)."""
        fixture = TB3_ROOT / "tb3-hashed-comment.hosts"
        assert fixture.is_file()
        cfg = load_config(CONFIG)
        expected = normalize_file(fixture, cfg)
        proc = run_normalize(fixture)
        assert proc.returncode == 0, proc.stderr
        got = OUTPUT.read_text(encoding="utf-8")
        assert got == expected
        assert "hidden-hash-comment" in got
