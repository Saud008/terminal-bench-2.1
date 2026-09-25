"""Behavioral verifier for irfs-stage initramfs manifest export."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_stager import (
    load_config,
    manifest_for_run,
    rootfs_digest,
    stage_rootfs,
    write_seed_rootfs,
)

APP = Path("/app")
FIXTURE_ROOT = APP / "fixtures" / "rootfs"
CONFIG = APP / "config" / "stage.json"
OUTPUT_PATH_STR = "/app/output/initramfs.manifest"
LEDGER_PATH_STR = "/app/state/irfs-ledger.jsonl"
MANIFEST_PATH_STR = "/app/state/irfs-manifest.json"
OUTPUT = Path(OUTPUT_PATH_STR)
LEDGER = Path(LEDGER_PATH_STR)
MANIFEST = Path(MANIFEST_PATH_STR)
CLI = APP / "bin" / "irfs-stage"
SEED = os.environ.get("VERIFIER_SEED", "initramfs-hook-order-firmware-stager")
TB3_ROOT = Path("/opt/verifier-fixtures/initramfs")

FIXTURES = sorted(p for p in FIXTURE_ROOT.iterdir() if p.is_dir())


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


def run_stage(rootfs: Path, output: Path = OUTPUT, config: Path = CONFIG) -> subprocess.CompletedProcess:
    return _run(
        [
            str(CLI),
            "--rootfs",
            str(rootfs),
            "--config",
            str(config),
            "--output",
            str(output),
        ]
    )


def expected_manifest(rootfs: Path, config: Path = CONFIG) -> str:
    cfg = load_config(config)
    text, _ = stage_rootfs(rootfs, cfg)
    return text


class TestStagerAntiCheat:
    """CLI-only checks that block shallow or hardcoded fixes."""

    def setup_method(self) -> None:
        reset_state()

    def test_seed_rootfs_matches_reference(self) -> None:
        """Seeded synthetic rootfs must match the independent reference stager output."""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_seed_rootfs(Path(tmp), SEED)
            expected = expected_manifest(root)
            proc = run_stage(root)
            assert proc.returncode == 0, proc.stderr
            assert OUTPUT.read_text(encoding="utf-8") == expected

    def test_catalog_and_seed_outputs_differ(self) -> None:
        """Anti-hardcode: seeded manifest bytes must differ from every bundled fixture."""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_seed_rootfs(Path(tmp), SEED)
            proc = run_stage(root)
            assert proc.returncode == 0, proc.stderr
            seed_out = OUTPUT.read_text(encoding="utf-8")
            for fixture in FIXTURES:
                reset_state()
                proc2 = run_stage(fixture)
                assert proc2.returncode == 0, proc2.stderr
                assert seed_out != OUTPUT.read_text(encoding="utf-8")

    def test_non_catalog_pci_id_selects_module(self) -> None:
        """Non-catalog PCI modalias and module name must still stage via live modalias rules."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "adhoc"
            (root / "hooks").mkdir(parents=True)
            (root / "etc" / "irfs").mkdir(parents=True)
            (root / "lib" / "modules" / "6.1.0" / "kernel" / "drivers" / "net").mkdir(parents=True)
            (root / "hooks" / "10-base.sh").write_text("#!/bin/sh\n# PREREQ=\n", encoding="utf-8")
            (root / "hooks" / "20-modules.sh").write_text(
                "#!/bin/sh\n# PREREQ=base\n# HOOK=modules\n", encoding="utf-8"
            )
            (root / "etc" / "irfs" / "modules.load").write_text("adhoc_net\n", encoding="utf-8")
            (root / "etc" / "irfs" / "pci.ids").write_text("pci:v0000ADH0d0000C0DE*\n", encoding="utf-8")
            (root / "lib" / "modules" / "6.1.0" / "modules.alias").write_text(
                "alias pci:v0000ADH0d0000C0DE* adhoc_net\n", encoding="utf-8"
            )
            (root / "lib" / "modules" / "6.1.0" / "kernel" / "drivers" / "net" / "adhoc_net.ko").write_text(
                "adhoc-ko", encoding="utf-8"
            )
            expected = expected_manifest(root)
            proc = run_stage(root)
            assert proc.returncode == 0, proc.stderr
            assert OUTPUT.read_text(encoding="utf-8") == expected
            assert "adhoc_net.ko" in OUTPUT.read_text(encoding="utf-8")


class TestInitramfsStager:
    """Verifier tests for irfs-stage."""

    def setup_method(self) -> None:
        reset_state()

    @pytest.mark.parametrize("fixture_path", FIXTURES, ids=lambda p: p.name)
    def test_fixture_matches_reference(self, fixture_path: Path) -> None:
        """Each catalog rootfs must match the independent reference manifest exporter."""
        expected = expected_manifest(fixture_path)
        proc = run_stage(fixture_path)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert OUTPUT == Path(OUTPUT_PATH_STR)
        got = OUTPUT.read_text(encoding="utf-8")
        assert got == expected

    def test_missing_rootfs_exits_nonzero(self) -> None:
        """Missing --rootfs directory must exit 1 per instruction error contract."""
        reset_state()
        proc = run_stage(APP / "fixtures" / "rootfs" / "missing-dir")
        assert proc.returncode == 1
        assert OUTPUT.read_text(encoding="utf-8") == ""

    def test_rerun_is_deterministic(self) -> None:
        """Repeated runs on the same rootfs must yield identical manifest bytes."""
        fixture = FIXTURE_ROOT / "002-firmware-chain"
        proc1 = run_stage(fixture)
        first = OUTPUT.read_bytes()
        proc2 = run_stage(fixture)
        second = OUTPUT.read_bytes()
        assert proc1.returncode == 0 and proc2.returncode == 0
        assert first == second

    def test_state_ledger_and_manifest_paths(self) -> None:
        """Ingest must materialize /app/state/irfs-ledger.jsonl and /app/state/irfs-manifest.json."""
        fixture = FIXTURE_ROOT / "002-firmware-chain"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        assert LEDGER.is_file(), f"staging ledger path must exist: {LEDGER_PATH_STR}"
        assert MANIFEST.is_file(), f"manifest seal path must exist: {MANIFEST_PATH_STR}"
        ledger_rows = [ln for ln in LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()]
        seal = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert len(ledger_rows) == seal["entry_count"]
        assert "hook_order" in seal and "rootfs_sha256" in seal

    def test_manifest_sorted_by_path(self) -> None:
        """Export manifest rows must be sorted by path using LC_ALL=C ordering."""
        fixture = FIXTURE_ROOT / "006-dual-module"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        paths = [ln.split("\t", 1)[0] for ln in OUTPUT.read_text(encoding="utf-8").splitlines() if ln]
        assert paths == sorted(paths)

    def test_002_includes_firmware_blob(self) -> None:
        """Firmware.map selection must stage lib/firmware blobs with firmware kind rows."""
        fixture = FIXTURE_ROOT / "002-firmware-chain"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        text = OUTPUT.read_text(encoding="utf-8")
        assert "lib/firmware/mellanox/mlx4_fw.bin" in text
        assert "\tfirmware\t" in text
        assert "\tgz\t" in text

    def test_003_alpha_before_zebra_tiebreak(self) -> None:
        """Equal PREREQ hooks must tie-break by NN prefix then hook name in sealed hook_order."""
        fixture = FIXTURE_ROOT / "003-prereq-tiebreak"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        order = manifest["hook_order"]
        assert order.index("alpha") < order.index("zebra")

    def test_004_modalias_glob_suffix(self) -> None:
        """modules.alias glob suffix patterns must match pci.ids lines without exact equality."""
        fixture = FIXTURE_ROOT / "004-modalias-glob"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        assert "qed.ko" in OUTPUT.read_text(encoding="utf-8")

    def test_005_uppercase_bin_compression(self) -> None:
        """Compression policy must lowercase extensions before mapping .bin to gz."""
        fixture = FIXTURE_ROOT / "005-compress-mix"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        fw_line = [
            ln for ln in OUTPUT.read_text(encoding="utf-8").splitlines() if "qed_fw.BIN" in ln
        ][0]
        assert "\tgz\t" in fw_line

    def test_006_dual_module_firmware_rows(self) -> None:
        """Multiple selected modules must each emit firmware rows when mapped."""
        fixture = FIXTURE_ROOT / "006-dual-module"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        lines = OUTPUT.read_text(encoding="utf-8").splitlines()
        fw = [ln for ln in lines if "\tfirmware\t" in ln]
        assert len(fw) == 2

    def test_ledger_manifest_matches_rootfs(self) -> None:
        """irfs-manifest.json seal must bind rootfs digest, ledger digest, and hook order."""
        fixture = FIXTURE_ROOT / "002-firmware-chain"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        assert MANIFEST.is_file()
        got = json.loads(MANIFEST.read_text(encoding="utf-8"))
        _, hook_order = stage_rootfs(fixture, load_config(CONFIG))
        expected = manifest_for_run(fixture, LEDGER, hook_order)
        assert got == expected

    def test_staging_ledger_jsonl_seq(self) -> None:
        """irfs-ledger.jsonl rows must carry monotonic seq starting at 1 during ingest."""
        fixture = FIXTURE_ROOT / "001-minimal"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        assert LEDGER.is_file()
        rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert rows[0]["seq"] == 1
        assert "kind" in rows[0] and "path" in rows[0]

    def test_hook_order_respects_prereq(self) -> None:
        """Topological hook order in manifest seal must honor PREREQ edges from hook scripts."""
        fixture = FIXTURE_ROOT / "002-firmware-chain"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        order = json.loads(MANIFEST.read_text(encoding="utf-8"))["hook_order"]
        assert order.index("base") < order.index("udev")
        assert order.index("udev") < order.index("modules")
        assert order.index("modules") < order.index("firmware")

    def test_module_rows_use_modules_hook_rank(self) -> None:
        """Module manifest rows must inherit hook_rank from the modules hook stage."""
        fixture = FIXTURE_ROOT / "001-minimal"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        mod_lines = [ln for ln in OUTPUT.read_text(encoding="utf-8").splitlines() if "\tmodule\t" in ln]
        assert mod_lines
        assert mod_lines[0].endswith("\t2")

    def test_second_run_refreshes_manifest(self) -> None:
        """A second rootfs run must re-seal irfs-manifest.json with a new rootfs_sha256."""
        first = FIXTURE_ROOT / "001-minimal"
        second = FIXTURE_ROOT / "004-modalias-glob"
        proc1 = run_stage(first)
        assert proc1.returncode == 0
        digest1 = json.loads(MANIFEST.read_text(encoding="utf-8"))["rootfs_sha256"]
        proc2 = run_stage(second)
        assert proc2.returncode == 0
        digest2 = json.loads(MANIFEST.read_text(encoding="utf-8"))["rootfs_sha256"]
        assert digest1 != digest2
        assert digest2 == rootfs_digest(second)

    def test_001_module_ko_compression_xz(self) -> None:
        """Kernel module .ko paths must receive xz compression tag from stage.json."""
        fixture = FIXTURE_ROOT / "001-minimal"
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        ko_line = [ln for ln in OUTPUT.read_text(encoding="utf-8").splitlines() if ".ko" in ln][0]
        assert "\txz\tmodule\t" in ko_line

    def test_empty_hooks_dir_writes_empty_manifest(self) -> None:
        """Rootfs with hooks directory but no hook scripts must emit an empty manifest file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "empty"
            root.mkdir()
            (root / "hooks").mkdir()
            proc = run_stage(root)
            assert proc.returncode == 0, proc.stderr
            assert OUTPUT.read_text(encoding="utf-8") == ""


@pytest.mark.skipif(not TB3_ROOT.is_dir(), reason="hidden fixtures only in image")
class TestInitramfsHiddenTraps:
    """Hidden verifier fixtures — independent failure modes from catalog inputs."""

    def setup_method(self) -> None:
        reset_state()

    def test_tb3_prereq_inversion_hook_order(self) -> None:
        """Hidden hook graph requires late before net even when NN prefix suggests otherwise."""
        fixture = TB3_ROOT / "tb3-prereq-inversion"
        assert fixture.is_dir()
        expected = expected_manifest(fixture)
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        got = OUTPUT.read_text(encoding="utf-8")
        assert got == expected
        order = json.loads(MANIFEST.read_text(encoding="utf-8"))["hook_order"]
        assert order.index("late") < order.index("net")

    def test_tb3_modalias_suffix_glob(self) -> None:
        """Hidden modalias pattern must match pci id only when glob suffix is honored."""
        fixture = TB3_ROOT / "tb3-modalias-suffix"
        assert fixture.is_dir()
        expected = expected_manifest(fixture)
        proc = run_stage(fixture)
        assert proc.returncode == 0, proc.stderr
        assert OUTPUT.read_text(encoding="utf-8") == expected
        assert "hidden_scsi.ko" in OUTPUT.read_text(encoding="utf-8")

    def test_tb3_no_hooks_config_omits_hook_rows(self) -> None:
        """Hidden include_hook_scripts=false config must omit hook rows but keep module rows."""
        fixture = TB3_ROOT / "tb3-no-hooks"
        hidden_cfg = TB3_ROOT / "tb3-no-hooks.json"
        assert fixture.is_dir() and hidden_cfg.is_file()
        expected, _ = stage_rootfs(fixture, load_config(hidden_cfg))
        proc = _run(
            [
                str(CLI),
                "--rootfs",
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
        assert "hooks/" not in got
        assert "nethid.ko" in got
