"""Milestone 1: quadlet parse and drop-in merge."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from reference_quadlet import TOUCH, build_parse_graph, load_cli_parse, run_cli_parse

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
STACK = Path(CATALOG["default_tree"])
DROPINS = Path(CATALOG["dropin_tree"])
SEED = os.environ.get("VERIFIER_SEED", "bash-podman-quadlet-unit-dependency-cycle-resolver")


@pytest.fixture(autouse=True)
def reset_touch() -> None:
    TOUCH.parent.mkdir(parents=True, exist_ok=True)
    TOUCH.write_text("", encoding="utf-8")


class TestMilestone1:
    def test_parse_cli_succeeds(self, tmp_path: Path) -> None:
        """parse exits 0 for the default stack tree."""
        out = tmp_path / "parse.json"
        proc = run_cli_parse(STACK, out)
        assert proc.returncode == 0, proc.stderr
        data = load_cli_parse(out)
        assert len(data["units"]) == 8

    def test_parse_matches_reference(self, tmp_path: Path) -> None:
        """CLI parse output matches independent reference merge."""
        out = tmp_path / "parse.json"
        run_cli_parse(STACK, out)
        cli = load_cli_parse(out)
        ref = build_parse_graph(STACK)
        assert set(cli["units"]) == set(ref["units"])
        for name, ref_meta in ref["units"].items():
            assert cli["units"][name] == ref_meta, name

    def test_dropin_lexicographic_order(self, tmp_path: Path) -> None:
        """Drop-in fragments apply in basename sort order."""
        out = tmp_path / "parse.json"
        run_cli_parse(DROPINS, out)
        one = load_cli_parse(out)["units"]["one.service"]
        assert one["service"]["EnvironmentFile"] == ["-/etc/one/env", "-/etc/one/override.env"]
        assert "two.service" in one["unit"]["After"]

    def test_parser_touch_records_fragments(self, tmp_path: Path) -> None:
        """Surface parser runs once per merged fragment path."""
        out = tmp_path / "parse.json"
        run_cli_parse(STACK, out)
        touched = {line.strip() for line in TOUCH.read_text(encoding="utf-8").splitlines() if line.strip()}
        assert any("api.container.d" in p for p in touched)

    def test_seed_synthetic_units_parsed(self, tmp_path: Path) -> None:
        """Seed-derived chained units parse without hardcoded names in lib."""
        tag = hashlib.sha256(SEED.encode()).hexdigest()[:6]
        copy = tmp_path / "seed-tree"
        (copy / "a.container.d").mkdir(parents=True)
        (copy / "a.container").write_text(
            "[Unit]\nDescription=Seed A\nWants=b.service\n"
            "[Service]\nRestart=always\n"
            "[Container]\nImage=localhost/a:1\nRestart=no\n",
            encoding="utf-8",
        )
        (copy / "b.container").write_text(
            "[Unit]\nDescription=Seed B\nAfter=a.service\n"
            "[Service]\nRestart=on-failure\n"
            "[Container]\nImage=localhost/b:1\nRestart=no\n",
            encoding="utf-8",
        )
        (copy / f"c-{tag}.container").write_text(
            "[Unit]\nDescription=Seed C\nAfter=b.service\nWants=a.service\n"
            "[Container]\nImage=localhost/c:1\n",
            encoding="utf-8",
        )
        out = tmp_path / "parse.json"
        proc = run_cli_parse(copy, out)
        assert proc.returncode == 0, proc.stderr
        units = load_cli_parse(out)["units"]
        assert f"c-{tag}.service" in units
        assert units["b.service"]["unit"]["After"] == ["a.service"]

    def test_copied_stack_independent(self, tmp_path: Path) -> None:
        """Copied stack with injected drop-in matches reference."""
        copy = tmp_path / "stack-copy"
        shutil.copytree(STACK, copy)
        drop = copy / "metrics.container.d"
        drop.mkdir()
        (drop / "99-late.conf").write_text("[Unit]\nWants=proxy.service\n", encoding="utf-8")
        out = tmp_path / "parse.json"
        proc = run_cli_parse(copy, out)
        assert proc.returncode == 0, proc.stderr
        assert load_cli_parse(out)["units"] == build_parse_graph(copy)["units"]
