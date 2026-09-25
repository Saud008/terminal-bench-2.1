"""Behavioral verifier for oasctl OpenAPI payload validation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from reference_validator import reference_validate, result_row, select_payloads

APP = Path("/app")
FIXTURES = APP / "fixtures"
CONFIG = APP / "config/oasctl.json"
SPEC = FIXTURES / "openapi.yaml"
PAYLOADS = FIXTURES / "payloads"
OUTPUT = APP / "output/validation-report.json"
RESET = APP / "scripts/reset-state.sh"
SEED = os.environ.get("VERIFIER_SEED", "oas-seed-4464")

PROTECTED_SHA256: dict[str, str] = {
    "openapi.yaml": "48de544921c746195af792c94cc139db2c8437e7271c9dddd6422c1fe53ce721",
    "payloads/valid-cat.json": "791cf3b1c32f93ce3a9b4aecc108e8a21c77281743a87e36ae6c10d809048ce3",
    "payloads/valid-dog.json": "fdb55f5605e32a746b70c377953707965ffe98375a0a612464ae3bb184c9620b",
    "payloads/pet-without-lives.json": "245b5a37ee7bef81779c73a40fdf12c66e788da4db80a265b3e7822ed6ff57e3",
    "payloads/null-email.json": "032f2150eda9be26803bb3481a07997aa9235c6c8c09ba2669556e474371472c",
    "payloads/employee-record.json": "dce1311ca8766be4692264c1abf0a97895afff269b934dc04dbf1288f166a4b5",
    "payloads/employee-missing-employee-id.json": "91d717a91d355148de9201574ecea1a35201aa04b71c9a47463c591ac5858b6b",
    "payloads/invalid-missing-name.json": "e3bf9a3c72bb4de177538214effdead18118450cdf7a4202b57b159af4535771",
    "payloads/invalid-wrong-discriminator.json": "75f9f47b8f151845cf8a67e475cdf173baeb90ca80ea5348eff718f8b22a24d5",
    "payloads/cyclic-contact.json": "a631697aefc494f195f766489f57c7c042795db3b7292f93bb1d61110aca62f7",
    "payloads/extra-field-cat.json": "1a223dd936be3ef9b57647b1bc83bd2fdef3bcfe67d042f3a3e493ee8e41b0b8",
    "payloads/pet-missing-id.json": "e83ff5bc8a9902976d5a5f0796e4c222eb19544552c2c76f573d8b3aca347797",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
    )


def reset_state() -> None:
    proc = _run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build_cli() -> None:
    proc = _run(
        ["go", "build", "-mod=readonly", "-o", "/usr/local/bin/oasctl", "./cmd/oasctl"],
        cwd=APP,
    )
    assert proc.returncode == 0, proc.stderr


def validate_report(
    output: Path = OUTPUT,
    config: Path = CONFIG,
) -> subprocess.CompletedProcess[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    return _run(
        [
            "oasctl",
            "validate",
            "--spec",
            str(SPEC),
            "--payload",
            str(PAYLOADS),
            "--config",
            str(config),
            "--output",
            str(output),
        ]
    )


def _write_config_with_seed(tmp: Path, seed: str) -> Path:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["seed"] = seed
    path = tmp / "oasctl.json"
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return path


class TestOasctlValidate:
    """End-to-end oasctl validate against independent reference."""

    @classmethod
    def setup_class(cls) -> None:
        reset_state()
        build_cli()

    def test_fixture_integrity_hashes(self) -> None:
        """Protected fixtures must not be modified."""
        for rel, expect in PROTECTED_SHA256.items():
            assert _sha256(FIXTURES / rel) == expect, f"fixture tampered: {rel}"

    def test_full_report_matches_reference(self) -> None:
        """Full-seed validation report must match independent reference."""
        proc = validate_report(OUTPUT)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_validate(CONFIG, SPEC, PAYLOADS)
        assert got == expect

    def test_null_email_accepted(self) -> None:
        """Nullable email union must accept JSON null."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            assert validate_report(out).returncode == 0
            row = result_row(json.loads(out.read_text(encoding="utf-8")), "null-email.json")
            assert row["valid"] is True

    def test_discriminator_merge_enforces_cat_body(self) -> None:
        """Discriminator mapping must merge CatBody and enforce additionalProperties."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            assert validate_report(out).returncode == 0
            doc = json.loads(out.read_text(encoding="utf-8"))
            assert result_row(doc, "valid-cat.json")["valid"] is True
            assert result_row(doc, "extra-field-cat.json")["valid"] is False

    def test_multihop_ref_requires_base_record_id(self) -> None:
        """Chained refs must surface BaseRecord required id before validation."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            assert validate_report(out).returncode == 0
            row = result_row(
                json.loads(out.read_text(encoding="utf-8")),
                "pet-missing-id.json",
            )
            assert row["valid"] is False
            assert any("missing required id" in err for err in row["errors"])

    def test_unknown_discriminator_invalid(self) -> None:
        """Unknown discriminator value must fail validation."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            assert validate_report(out).returncode == 0
            row = result_row(
                json.loads(out.read_text(encoding="utf-8")),
                "invalid-wrong-discriminator.json",
            )
            assert row["valid"] is False
            assert any("unknown discriminator" in err for err in row["errors"])

    def test_allof_employee_record_valid(self) -> None:
        """Merged EmployeeRecord schema must accept name and employeeId."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            assert validate_report(out).returncode == 0
            row = result_row(json.loads(out.read_text(encoding="utf-8")), "employee-record.json")
            assert row["valid"] is True

    def test_employee_missing_employee_id_invalid(self) -> None:
        """Employee fragment required employeeId must be enforced after allOf merge."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            assert validate_report(out).returncode == 0
            row = result_row(
                json.loads(out.read_text(encoding="utf-8")),
                "employee-missing-employee-id.json",
            )
            assert row["valid"] is False
            assert any("missing required employeeId" in err for err in row["errors"])

    def test_cyclic_ref_records_cycle(self) -> None:
        """Cyclic Contact/profile refs must record at least one cycle."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            assert validate_report(out).returncode == 0
            row = result_row(json.loads(out.read_text(encoding="utf-8")), "cyclic-contact.json")
            assert row["valid"] is True
            assert row["cycles_seen"] >= 1

    def test_missing_required_name_invalid(self) -> None:
        """Missing required name must invalidate pet payload."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            assert validate_report(out).returncode == 0
            row = result_row(
                json.loads(out.read_text(encoding="utf-8")),
                "invalid-missing-name.json",
            )
            assert row["valid"] is False

    def test_seed_subset_matches_reference(self) -> None:
        """oas-seed-64 subset must match reference bundle selection and matrix."""
        subset_seed = "oas-seed-64"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out = tmp_path / "sub.json"
            subset_cfg = _write_config_with_seed(tmp_path, subset_seed)
            assert validate_report(out, subset_cfg).returncode == 0
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_validate(subset_cfg, SPEC, PAYLOADS)
            assert got == expect
            cfg_payloads = json.loads(CONFIG.read_text(encoding="utf-8"))["payloads"]
            assert got["payloads"] == select_payloads(subset_seed, cfg_payloads)
            assert len(got["payloads"]) == 2
            assert got["payloads"] != select_payloads(SEED, cfg_payloads)

    def test_stats_valid_invalid_counts(self) -> None:
        """Full seed stats must count six valid and five invalid payloads."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            assert validate_report(out).returncode == 0
            doc = json.loads(out.read_text(encoding="utf-8"))
            assert doc["stats"] == {"validated": 11, "valid": 6, "invalid": 5}
            assert doc["seed"] == SEED
