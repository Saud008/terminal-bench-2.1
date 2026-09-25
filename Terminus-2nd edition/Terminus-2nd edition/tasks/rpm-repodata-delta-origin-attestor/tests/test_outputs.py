"""Behavioral tests for rpm-repo-attest offline RPM origin attestor."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from reference_attest import reference_export

CLI = "/app/bin/rpm-repo-attest"
STAGE = Path("/app/state/repo-stage.json")
EXPORT = Path("/app/output/repo-attestation.json")
BASELINE = Path("/app/fixtures/repos/baseline")
LINEAGE = Path("/app/fixtures/repos/lineage")
TB3 = Path("/opt/verifier-fixtures/repos/tb3-gamma")
GOLDEN = Path(__file__).resolve().parent / "golden_lib"
BROKEN = Path(__file__).resolve().parent / "broken_lib"
LIB = Path("/app/lib")


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _fresh() -> None:
    for p in (STAGE, EXPORT):
        if p.exists():
            p.unlink()


def _ingest(repo: Path, mirror: Path) -> None:
    _run([CLI, "ingest", str(repo), "--mirror-manifest", str(mirror)])


def _export(out: Path | None = None) -> None:
    out = out or EXPORT
    _run([CLI, "export", "attestation", "--out", str(out)])


def _pipeline(repo: Path, mirror: Path) -> None:
    _fresh()
    _ingest(repo, mirror)
    _export()


def snapshot_lib() -> dict[str, str]:
    names = ["repomd.sh", "primary.sh", "modules.sh", "mirror.sh", "lineage.sh", "export.sh"]
    return {name: (LIB / name).read_text(encoding="utf-8") for name in names}


def restore_lib(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        (LIB / name).write_text(content, encoding="utf-8")


def restore_broken_lib() -> None:
    for src in BROKEN.glob("*.sh"):
        data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        (LIB / src.name).write_bytes(data)


def install_golden(name: str) -> None:
    src = GOLDEN / name
    if src.is_file():
        (LIB / name).write_bytes(src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))


@pytest.fixture(autouse=True)
def clean_state() -> None:
    _fresh()
    yield
    _fresh()


@pytest.fixture(autouse=True)
def _restore_lib() -> None:
    saved = snapshot_lib()
    yield
    restore_lib(saved)


def test_cli_binary_exists() -> None:
    """Instruction requires rpm-repo-attest CLI at /app/bin/rpm-repo-attest."""
    assert Path(CLI).is_file()


def test_baseline_fixture_tree_exists() -> None:
    """fixture-catalog.md cites baseline repodata and mirror snapshot fixtures."""
    assert (BASELINE / "repodata/repomd.xml").is_file()
    assert (BASELINE / "mirror-snapshot.json").is_file()


def test_ingest_writes_staging_snapshot() -> None:
    """Ingest must materialize normalized staging at /app/state/repo-stage.json."""
    _ingest(BASELINE, BASELINE / "mirror-snapshot.json")
    assert STAGE.is_file()
    data = json.loads(STAGE.read_text(encoding="utf-8"))
    assert data["repo_id"] == "baseline"


def test_ingest_seq_monotonic() -> None:
    """Staging ingest_seq must increment on every ingest call."""
    mirror = BASELINE / "mirror-snapshot.json"
    _ingest(BASELINE, mirror)
    first = json.loads(STAGE.read_text(encoding="utf-8"))["ingest_seq"]
    _ingest(BASELINE, mirror)
    second = json.loads(STAGE.read_text(encoding="utf-8"))["ingest_seq"]
    assert second == first + 1


def test_export_attestation_creates_output() -> None:
    """export attestation must write repo-attestation.json under /app/output."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    assert EXPORT.is_file()


def test_baseline_checksum_ok() -> None:
    """repomd-checksum-contract.md requires checksum_ok true when digests match."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert got["checksum_ok"] is True


def test_baseline_mirror_snapshot_valid() -> None:
    """mirror-snapshot-staleness.md accepts baseline mirror when revision aligns."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert got["mirror_snapshot_valid"] is True


def test_widget_lineage_epoch_one_is_rank_one() -> None:
    """nevra-lineage-order.md ranks epoch 1 widget ahead of epoch 0 sibling."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    widgets = [p for p in got["packages"] if p["name"] == "acme-widget"]
    rank1 = next(p for p in widgets if p["lineage_rank"] == 1)
    assert rank1["epoch"] == 1
    assert rank1["version"] == "2.10"


def test_widget_nevra_includes_epoch_prefix() -> None:
    """nevra-lineage-order.md requires epoch prefix in every nevra key string."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    newest = next(p for p in got["packages"] if p["name"] == "acme-widget" and p["lineage_rank"] == 1)
    assert newest["nevra"].startswith("1:acme-widget-")


def test_module_defaults_httpd_stream() -> None:
    """modulemd-default-stream.md exports httpd stream_name 2.4 and default profile."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    httpd = next(m for m in got["module_defaults"] if m["module"] == "httpd")
    assert httpd["default_stream"] == "2.4"
    assert httpd["default_profile"] == "default"


def test_module_defaults_nginx_stream() -> None:
    """modulemd-default-stream.md exports nginx stable stream and common profile."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    nginx = next(m for m in got["module_defaults"] if m["module"] == "nginx")
    assert nginx["default_stream"] == "stable"
    assert nginx["default_profile"] == "common"


def test_baseline_full_export_matches_reference() -> None:
    """Independent reference agrees with subprocess ingest and export on baseline."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGE)
    assert got == ref


def test_lineage_repo_version_ordering_trap() -> None:
    """nevra-lineage-order.md EVRA ordering ranks 10.1 ahead of lexically higher 9.99."""
    _pipeline(LINEAGE, LINEAGE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    pkg = next(p for p in got["packages"] if p["name"] == "sortable-pkg" and p["lineage_rank"] == 1)
    assert pkg["version"] == "10.1"


def test_stale_mirror_marks_invalid_in_staging() -> None:
    """mirror-snapshot-staleness.md rejects mirror-stale.json revision mismatch."""
    _ingest(BASELINE, BASELINE / "mirror-stale.json")
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    assert stage["mirror_snapshot_valid"] is False


def test_export_packages_sorted_by_nevra() -> None:
    """attestation-export-schema.md requires packages sorted by nevra ascending."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    nevras = [p["nevra"] for p in got["packages"]]
    assert nevras == sorted(nevras)


def test_origin_digest_matches_reference() -> None:
    """attestation-export-schema.md sha256 origin_digest matches independent reference."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGE)
    assert got["origin_digest"] == ref["origin_digest"]
    assert got["origin_digest"].startswith("sha256:")


def test_export_output_path_contract() -> None:
    """Instruction fixes export output path at /app/output/repo-attestation.json."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    assert str(EXPORT) == "/app/output/repo-attestation.json"


def test_staging_path_contract() -> None:
    """Instruction fixes staging snapshot path at /app/state/repo-stage.json."""
    _ingest(BASELINE, BASELINE / "mirror-snapshot.json")
    assert STAGE == Path("/app/state/repo-stage.json")


def test_tb3_hidden_zeta_crate_nevra_epoch() -> None:
    """Hidden tb3-gamma repo verifies epoch 2 nevra without bundled package names."""
    _pipeline(TB3, TB3 / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGE)
    crate = next(p for p in got["packages"] if p["name"] == "zeta-crate")
    assert crate["epoch"] == 2
    assert crate["nevra"] == "2:zeta-crate-1.0-1.el9.x86_64"
    assert got == ref


def test_tb3_hidden_module_defaults() -> None:
    """Hidden tb3-gamma modules.yaml exports hidden-mod tb3-stream defaults."""
    _pipeline(TB3, TB3 / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    mod = next(m for m in got["module_defaults"] if m["module"] == "hidden-mod")
    assert mod["default_stream"] == "tb3-stream"


class TestPartialFixTraps:
    def test_partial_golden_repomd_only_still_fails_digest(self, tmp_path: Path) -> None:
        """Probe: repomd-only patch leaves lineage modules export digest wrong."""
        restore_broken_lib()
        install_golden("repomd.sh")
        out = tmp_path / "partial-repomd.json"
        _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
        ref = reference_export(STAGE)
        _export(out)
        got = json.loads(out.read_text(encoding="utf-8"))
        assert got["checksum_ok"] is True
        assert got != ref

    def test_partial_golden_lineage_only_still_fails_modules(self, tmp_path: Path) -> None:
        """Probe: lineage-only patch still fails modulemd default_stream contract."""
        restore_broken_lib()
        install_golden("lineage.sh")
        out = tmp_path / "partial-lineage.json"
        _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
        ref = reference_export(STAGE)
        _export(out)
        got = json.loads(out.read_text(encoding="utf-8"))
        httpd = next(m for m in got["module_defaults"] if m["module"] == "httpd")
        assert httpd["default_stream"] != "2.4"
        assert got != ref

    def test_export_reads_staging_not_live_mirror(self, tmp_path: Path) -> None:
        """export attestation must read mirror_snapshot_valid from staging only."""
        _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
        stage = json.loads(STAGE.read_text(encoding="utf-8"))
        stage["mirror_snapshot_valid"] = False
        STAGE.write_text(json.dumps(stage, indent=2) + "\n", encoding="utf-8")
        out = tmp_path / "staged-mirror.json"
        _export(out)
        got = json.loads(out.read_text(encoding="utf-8"))
        assert got["mirror_snapshot_valid"] is False


def test_independent_reference_subprocess_pipeline() -> None:
    """Subprocess CLI pipeline must match reference_attest export for baseline."""
    _pipeline(BASELINE, BASELINE / "mirror-snapshot.json")
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert got == reference_export(STAGE)
