"""Hidden TB3 wgpatlas trap tests."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from wgpatlas_cli_support import APP, CLI, run_pipeline, wipe, invoke
from wgpatlas_contract_math import reference_atlas


def _overlay_hidden(site: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-wgp-"))
    src = Path("/opt/verifier-fixtures/wgpatlas/sites") / site
    dst = tmp / site
    shutil.copytree(src, dst)
    return tmp


def test_hidden_tb3_randomized_endpoint_and_disabled():
    """Verify TB3 randomized mesh atlas matches reference with TB3_SITE_ROOT overlay."""
    wipe()
    root = _overlay_hidden("tb3-randomized-mesh")
    site_dir = root / "tb3-randomized-mesh"
    out = run_pipeline("tb3-randomized-mesh", "run-h1", site_root=root)
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(site_dir, "run-h1")
    assert rep == {k: v for k, v in ref.items() if not k.startswith("_")}


def test_hidden_tb3_overlap_trap_subnet():
    """Verify TB3 overlap trap detects subnet overlap independent of bundled coastal-mesh keys."""
    wipe()
    root = _overlay_hidden("tb3-overlap-trap")
    site_dir = root / "tb3-overlap-trap"
    out = run_pipeline("tb3-overlap-trap", "run-h2", site_root=root)
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_atlas(site_dir, "run-h2")
    assert len(rep["overlaps"]) == len(ref["overlaps"])
    assert len(ref["overlaps"]) >= 1


def test_hidden_multi_allowed_ips_ingest_workspace():
    """Verify hidden rand-alpha retains two AllowedIPs CIDRs in workspace after ingest and analyze."""
    wipe()
    root = _overlay_hidden("tb3-randomized-mesh")
    env = {"TB3_SITE_ROOT": str(root)}
    invoke([str(CLI), "ingest", "--site", "tb3-randomized-mesh", "--run-id", "run-h3"], env=env)
    invoke([str(CLI), "analyze", "--run-id", "run-h3"], env=env)
    snap = json.loads((APP / "state" / "wgpatlas-workspace.json").read_text(encoding="utf-8"))
    alpha = next(p for p in snap["peers"] if p["peer_id"] == "rand-alpha")
    assert len(alpha["allowed_ips"]) == 2
