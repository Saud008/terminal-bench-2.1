"""Milestone 1: PipelineRun parse and task DAG order."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from cli_helpers import run_cli
from reference_planner import inject_task_suffix, reference_parse

APP = Path("/app")
FIXTURES = APP / "fixtures"
CANONICAL = Path("/opt/verifier-fixtures")
MANIFEST = CANONICAL / "fixtures.sha256"
CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
SEED = os.environ.get("VERIFIER_SEED", CATALOG["seed"])


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(directory: Path, manifest_path: Path) -> None:
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        target = directory / name.strip()
        assert sha256_file(target) == digest


def suffix_token() -> str:
    return format(int(SEED, 16) % 10000, "04x")


class TestMilestone1:
    def test_fixture_integrity(self) -> None:
        """Public fixtures match build-time manifest."""
        verify_manifest(FIXTURES, MANIFEST)
        verify_manifest(CANONICAL, MANIFEST)

    def test_task_order_topological_not_alphabetical(self) -> None:
        """task_order respects runAfter instead of sorting names."""
        fixture = FIXTURES / CATALOG["parse_fixture"]
        expected = reference_parse(fixture)
        actual = run_cli("parse", fixture)
        assert actual["task_order"] == expected["task_order"]

    def test_workspace_optional_flag_parsed(self) -> None:
        """optional workspace declarations are preserved."""
        fixture = FIXTURES / CATALOG["optional_fixture"]
        expected = reference_parse(fixture)
        actual = run_cli("parse", fixture)
        assert actual["workspace_declarations"] == expected["workspace_declarations"]
        signing = next(d for d in actual["workspace_declarations"] if d["name"] == "signing-key")
        assert signing["optional"] is True

    def test_injected_task_names_preserve_order(self) -> None:
        """Mutated task names still produce correct topological order."""
        src = FIXTURES / CATALOG["parse_fixture"]
        token = suffix_token()
        dest = Path("/tmp") / f"dag-order-{token}.yaml"
        inject_task_suffix(src, token, dest)
        expected = reference_parse(dest)
        actual = run_cli("parse", dest)
        assert actual["task_order"] == expected["task_order"]

    def test_rebuild_succeeds(self) -> None:
        """CLI binary rebuilds after source edits."""
        proc = subprocess.run(["bash", str(APP / "scripts" / "verifier-rebuild.sh")], check=False)
        assert proc.returncode == 0
