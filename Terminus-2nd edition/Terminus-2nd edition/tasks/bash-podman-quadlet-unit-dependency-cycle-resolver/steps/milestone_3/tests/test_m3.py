"""Milestone 3: systemd unit render and verify."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from reference_quadlet import parse_unit, render_reference, run_cli_render

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
STACK = Path(CATALOG["default_tree"])
DROPINS = Path(CATALOG["dropin_tree"])
CYCLE = Path(CATALOG["cycle_tree"])
SEED = os.environ.get("VERIFIER_SEED", "bash-podman-quadlet-unit-dependency-cycle-resolver")


class TestMilestone3:
    def test_render_stack_matches_reference(self, tmp_path: Path) -> None:
        """render output matches independent reference units."""
        out = tmp_path / "units"
        proc = run_cli_render(STACK, out)
        assert proc.returncode == 0, proc.stderr
        ref_dir = tmp_path / "ref"
        render_reference(STACK, ref_dir)
        for path in sorted(ref_dir.glob("*.service")):
            assert path.name in {p.name for p in out.glob("*.service")}
            assert path.read_text(encoding="utf-8") == (out / path.name).read_text(encoding="utf-8")

    def test_environment_file_propagated(self, tmp_path: Path) -> None:
        """Generated units include merged EnvironmentFile lines."""
        out = tmp_path / "units"
        run_cli_render(DROPINS, out)
        svc = parse_unit(out / "one.service")
        assert svc["Service"]["EnvironmentFile"] == ["-/etc/one/env", "-/etc/one/override.env"]

    def test_restart_from_service_not_container(self, tmp_path: Path) -> None:
        """Restart= comes from [Service], ignoring [Container] Restart=."""
        out = tmp_path / "units"
        run_cli_render(DROPINS, out)
        one = parse_unit(out / "one.service")
        two = parse_unit(out / "two.service")
        assert one["Service"]["Restart"] == "always"
        assert two["Service"]["Restart"] == "on-failure"

    def test_systemd_analyze_verify(self, tmp_path: Path) -> None:
        """Rendered stack units pass systemd-analyze verify."""
        out = tmp_path / "units"
        proc = run_cli_render(STACK, out)
        assert proc.returncode == 0, proc.stderr
        for unit in sorted(out.glob("*.service")):
            check = subprocess.run(
                ["systemd-analyze", "verify", str(unit)],
                capture_output=True,
                text=True,
                check=False,
            )
            assert check.returncode == 0, check.stderr or check.stdout

    def test_render_cycle_exits_two(self, tmp_path: Path) -> None:
        """render aborts on dependency cycle without writing unit files."""
        out = tmp_path / "units"
        proc = run_cli_render(CYCLE, out)
        assert proc.returncode == 2
        assert "cycle:" in proc.stderr
        assert not list(out.glob("*.service"))

    def test_after_wants_present_in_emitted_unit(self, tmp_path: Path) -> None:
        """Emitted [Unit] carries merged After= and Wants= from parse."""
        out = tmp_path / "units"
        run_cli_render(STACK, out)
        api = parse_unit(out / "api.service")
        assert "db.service" in api["Unit"]["Wants"]
        assert "auth.service" in api["Unit"]["After"]

    def test_seed_chained_render(self, tmp_path: Path) -> None:
        """Seed-derived chain renders three units with correct Restart policy."""
        tag = hashlib.sha256(f"{SEED}:render".encode()).hexdigest()[:6]
        copy = tmp_path / "seed-render"
        copy.mkdir()
        for name, restart, after in (
            (f"a-{tag}", "always", ""),
            (f"b-{tag}", "on-failure", f"a-{tag}.service"),
            (f"c-{tag}", "always", f"b-{tag}.service"),
        ):
            after_line = f"After={after}\n" if after else ""
            (copy / f"{name}.container").write_text(
                f"[Unit]\nDescription={name}\n{after_line}"
                f"[Service]\nEnvironmentFile=-/etc/{name}/env\nRestart={restart}\n"
                f"[Container]\nImage=localhost/{name}:1\nRestart=no\n",
                encoding="utf-8",
            )
        out = tmp_path / "units"
        proc = run_cli_render(copy, out)
        assert proc.returncode == 0, proc.stderr
        c_unit = parse_unit(out / f"c-{tag}.service")
        assert c_unit["Service"]["Restart"] == "always"
        assert c_unit["Service"]["EnvironmentFile"] == [f"-/etc/c-{tag}/env"]

    def test_render_does_not_mutate_fixtures(self, tmp_path: Path) -> None:
        """render leaves fixture tree byte-identical."""
        copy = tmp_path / "stack-copy"
        shutil.copytree(STACK, copy)
        before = {p.relative_to(copy): p.read_bytes() for p in copy.rglob("*") if p.is_file()}
        out = tmp_path / "units"
        run_cli_render(copy, out)
        after = {p.relative_to(copy): p.read_bytes() for p in copy.rglob("*") if p.is_file()}
        assert before == after
