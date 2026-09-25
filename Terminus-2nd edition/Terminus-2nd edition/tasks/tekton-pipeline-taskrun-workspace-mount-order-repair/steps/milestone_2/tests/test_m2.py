"""Milestone 2: workspace binding resolution."""

from __future__ import annotations

import json
import os
from pathlib import Path

from cli_helpers import run_cli
from reference_planner import inject_workspace_claim, reference_bind

APP = Path("/app")
FIXTURES = APP / "fixtures"
CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
SEED = os.environ.get("VERIFIER_SEED", CATALOG["seed"])


def suffix_token() -> str:
    return format(int(SEED, 16) % 10000, "04x")


class TestMilestone2:
    def test_pvc_and_emptydir_kinds_not_swapped(self) -> None:
        """Pipeline bindings keep PVC vs emptyDir kinds."""
        fixture = FIXTURES / CATALOG["binding_fixture"]
        expected = reference_bind(fixture)
        actual = run_cli("bind", fixture)
        build_ws = next(t for t in actual["tasks"] if t["name"] == "build")
        cache = next(w for w in build_ws["workspaces"] if w["task_workspace"] == "cache")
        creds = next(w for w in build_ws["workspaces"] if w["task_workspace"] == "creds")
        assert cache["source"]["kind"] == "persistentVolumeClaim"
        assert cache["source"]["claim_name"] == "cache-pvc-01"
        assert creds["source"]["kind"] == "emptyDir"
        assert creds["source"]["medium"] == "Memory"
        assert json.dumps(actual["tasks"], sort_keys=True) == json.dumps(expected["tasks"], sort_keys=True)

    def test_pipeline_workspace_lookup_by_pipeline_name(self) -> None:
        """Bindings resolve via pipeline workspace name, not task-local name."""
        fixture = FIXTURES / CATALOG["binding_fixture"]
        actual = run_cli("bind", fixture)
        build_ws = next(t for t in actual["tasks"] if t["name"] == "build")
        cache = next(w for w in build_ws["workspaces"] if w["task_workspace"] == "cache")
        assert cache["pipeline_workspace"] == "shared-cache"
        assert cache["skipped"] is False

    def test_optional_workspace_skipped_when_unbound(self) -> None:
        """Optional pipeline workspaces without bindings are skipped."""
        fixture = FIXTURES / CATALOG["optional_fixture"]
        actual = run_cli("bind", fixture)
        pkg = next(t for t in actual["tasks"] if t["name"] == "package")
        key = next(w for w in pkg["workspaces"] if w["task_workspace"] == "key")
        assert key["skipped"] is True
        assert key.get("source") is None
        dist = next(w for w in pkg["workspaces"] if w["task_workspace"] == "dist")
        assert dist["source"]["kind"] == "emptyDir"
        assert dist["skipped"] is False

    def test_mutated_claim_name_propagates(self) -> None:
        """Injected PVC claim suffix flows through bind output."""
        src = FIXTURES / CATALOG["binding_fixture"]
        token = suffix_token()
        dest = Path("/tmp") / f"binding-mix-{token}.yaml"
        inject_workspace_claim(src, token, dest)
        expected = reference_bind(dest)
        actual = run_cli("bind", dest)
        build_ws = next(t for t in actual["tasks"] if t["name"] == "build")
        cache = next(w for w in build_ws["workspaces"] if w["task_workspace"] == "cache")
        assert cache["source"]["claim_name"] == f"cache-pvc-01-{token}"
        assert json.dumps(actual["tasks"], sort_keys=True) == json.dumps(expected["tasks"], sort_keys=True)
