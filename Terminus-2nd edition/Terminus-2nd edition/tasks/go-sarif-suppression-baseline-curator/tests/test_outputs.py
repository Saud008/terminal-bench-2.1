"""Legacy verifier entry filename — artifact paths plus reference-backed digest smoke."""

from __future__ import annotations

import json
import subprocess

from sarbctl_curator_contract import compute_findings_digest, load_sarif_findings
from sarbctl_runner import DELTA_OUT, SARIF, sarbctl_full_run


def test_t5e5401_outputs_reference_digest_and_delta_paths(clean_workspace: None) -> None:
    """Instruction paths exist and scan findings_digest matches sarbctl_curator_contract."""
    proc = subprocess.run(
        ["test", "-x", "/usr/local/bin/sarbctl"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, "sarbctl must be built before pytest"
    sarbctl_full_run(SARIF, __import__("sarbctl_runner").POLICY, __import__("sarbctl_runner").REMAP, __import__("sarbctl_runner").BASELINE)
    findings = load_sarif_findings(SARIF)
    staging = json.loads((__import__("sarbctl_runner").STAGING).read_text(encoding="utf-8"))
    assert staging["findings_digest"] == compute_findings_digest(findings)
    assert len(json.loads(DELTA_OUT.read_text(encoding="utf-8"))["delta_digest"]) == 64
