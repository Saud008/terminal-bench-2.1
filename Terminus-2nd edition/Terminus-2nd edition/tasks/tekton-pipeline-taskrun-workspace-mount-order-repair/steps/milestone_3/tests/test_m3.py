"""Milestone 3: mount plan DAG and subpath ordering."""

from __future__ import annotations

import json
import os
from pathlib import Path

from cli_helpers import run_cli
from reference_planner import inject_step_suffix, reference_plan

APP = Path("/app")
FIXTURES = APP / "fixtures"
CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
SEED = os.environ.get("VERIFIER_SEED", CATALOG["seed"])


def suffix_token() -> str:
    return format(int(SEED, 16) % 10000, "04x")


class TestMilestone3:
    def test_step_runafter_topological_order(self) -> None:
        """Mount entries follow step runAfter DAG, not alphabetical names."""
        fixture = FIXTURES / CATALOG["plan_fixture"]
        expected = reference_plan(fixture)
        actual = run_cli("plan", fixture)
        steps = [m["step"] for m in actual["mounts"]]
        seen: list[str] = []
        for step in steps:
            if step not in seen:
                seen.append(step)
        assert seen == ["write", "pack", "verify"]
        assert len(steps) == 6
        assert actual["mounts"] == expected["mounts"]

    def test_parent_mount_before_subpath(self) -> None:
        """Root workspace mount precedes subPath mount within each step."""
        fixture = FIXTURES / CATALOG["plan_fixture"]
        actual = run_cli("plan", fixture)
        for step in {"write", "pack", "verify"}:
            step_mounts = [m for m in actual["mounts"] if m["step"] == step]
            assert len(step_mounts) == 2
            assert step_mounts[0].get("sub_path", "") == ""
            assert step_mounts[0]["mount_path"] == "/workspaces/ws"
            assert step_mounts[1]["sub_path"] == "output"
            assert step_mounts[1]["mount_path"] == "/workspaces/ws/output"

    def test_task_dag_order_in_full_plan(self) -> None:
        """Tasks with dependencies appear before dependents in mount list."""
        fixture = FIXTURES / CATALOG["dag_fixture"]
        actual = run_cli("plan", fixture)
        task_names = [m["task"] for m in actual["mounts"]]
        assert task_names == ["fetch", "compile", "publish"]

    def test_injected_step_names_keep_mount_order(self) -> None:
        """Mutated step names preserve topological mount sequencing."""
        src = FIXTURES / CATALOG["plan_fixture"]
        token = suffix_token()
        dest = Path("/tmp") / f"subpath-steps-{token}.yaml"
        inject_step_suffix(src, token, dest)
        expected = reference_plan(dest)
        actual = run_cli("plan", dest)
        assert actual["mounts"] == expected["mounts"]

    def test_skipped_optional_emits_no_mounts(self) -> None:
        """Optional unbound workspaces produce no mount rows."""
        fixture = FIXTURES / "optional-skip.yaml"
        actual = run_cli("plan", fixture)
        workspaces = {m["workspace"] for m in actual["mounts"]}
        assert "key" not in workspaces
        assert all(m.get("kind") for m in actual["mounts"])
