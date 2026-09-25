"""Milestone 2: directed DAG cycle detection and topological order."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from reference_quadlet import (
    build_parse_graph,
    build_edges,
    find_cycle,
    run_cli_order,
    topo_order,
)

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
STACK = Path(CATALOG["default_tree"])
DROPINS = Path(CATALOG["dropin_tree"])
CYCLE = Path(CATALOG["cycle_tree"])
SEED = os.environ.get("VERIFIER_SEED", "bash-podman-quadlet-unit-dependency-cycle-resolver")


def assert_order_valid(order: list[str], units: dict) -> None:
    pos = {name: i for i, name in enumerate(order)}
    assert len(order) == len(units)
    edges = build_edges(units)
    for unit, deps in edges.items():
        for dep in deps:
            assert pos[dep] < pos[unit], f"{dep} must precede {unit}"


class TestMilestone2:
    def test_order_matches_reference(self, tmp_path: Path) -> None:
        """order JSON matches independent topological reference."""
        out = tmp_path / "order.json"
        proc = run_cli_order(STACK, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))["order"]
        ref_units = build_parse_graph(STACK)["units"]
        assert cli == topo_order(ref_units)

    def test_order_respects_edges(self, tmp_path: Path) -> None:
        """Every dependency edge places its tail before its head."""
        out = tmp_path / "order.json"
        run_cli_order(STACK, out)
        order = json.loads(out.read_text(encoding="utf-8"))["order"]
        units = build_parse_graph(STACK)["units"]
        assert_order_valid(order, units)

    def test_lexicographic_tie_break(self, tmp_path: Path) -> None:
        """Independent roots sort lexicographically (db before redis)."""
        out = tmp_path / "order.json"
        run_cli_order(STACK, out)
        order = json.loads(out.read_text(encoding="utf-8"))["order"]
        assert order.index("db.service") < order.index("redis.service")

    def test_wants_only_not_false_cycle(self, tmp_path: Path) -> None:
        """Wants-only edge must not invent reverse dependency cycle."""
        out = tmp_path / "order.json"
        proc = run_cli_order(DROPINS, out)
        assert proc.returncode == 0, proc.stderr
        order = json.loads(out.read_text(encoding="utf-8"))["order"]
        assert order.index("two.service") < order.index("one.service")

    def test_cycle_exits_two(self, tmp_path: Path) -> None:
        """Built-in cycle fixture exits 2 with cycle stderr."""
        out = tmp_path / "order.json"
        proc = run_cli_order(CYCLE, out)
        assert proc.returncode == 2
        assert proc.stderr.strip().startswith("cycle:")
        ref = find_cycle(build_parse_graph(CYCLE)["units"])
        assert ref is not None
        reported = proc.stderr.strip().split(":", 1)[1]
        assert reported.startswith(ref[0])

    def test_injected_cycle_detected(self, tmp_path: Path) -> None:
        """Seed-injected cycle pair is detected in a copied tree."""
        tag = hashlib.sha256(SEED.encode()).hexdigest()[:6]
        copy = tmp_path / "seed-cycle"
        copy.mkdir()
        (copy / f"x-{tag}.container").write_text(
            f"[Unit]\nAfter=y-{tag}.service\n[Container]\nImage=localhost/x:1\n",
            encoding="utf-8",
        )
        (copy / f"y-{tag}.container").write_text(
            f"[Unit]\nAfter=x-{tag}.service\n[Container]\nImage=localhost/y:1\n",
            encoding="utf-8",
        )
        out = tmp_path / "order.json"
        proc = run_cli_order(copy, out)
        assert proc.returncode == 2
        assert f"x-{tag}" in proc.stderr and f"y-{tag}" in proc.stderr

    def test_eight_unit_stack_complete(self, tmp_path: Path) -> None:
        """Stack fixture emits all eight units in valid order."""
        out = tmp_path / "order.json"
        proc = run_cli_order(STACK, out)
        assert proc.returncode == 0, proc.stderr
        order = json.loads(out.read_text(encoding="utf-8"))["order"]
        assert len(order) == 8
        units = build_parse_graph(STACK)["units"]
        assert_order_valid(order, units)
        assert order.index("proxy.service") < order.index("frontend.service")
        assert order.index("db.service") < order.index("auth.service")
