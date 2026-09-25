"""Hidden TB3 permutation salt trap tests for inference-time feature eval."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from minclus_run import run_pipeline, wipe
from minhash_ref import reference_report


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


class TestMinclusTb3Traps:
    def test_tb3_perm_salt_changes_clustering(self):
        """TB3_PERM_SALT must alter MinHash signatures and clustering outcome."""
        tb3_dir = Path("/opt/verifier-fixtures/minclus/corpora")
        run_id = "run-tb3-salt"
        env = {"TB3_PERM_SALT": "shift-7", "TB3_CORPUS_DIR": str(tb3_dir)}
        out = run_pipeline(run_id, "tb3-salt-shift", floor=0.5, env=env)
        rep = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_report(
            run_id,
            tb3_dir / "tb3-salt-shift",
            salt="shift-7",
        )
        assert rep["audit_digest"] == ref["audit_digest"]

    def test_tb3_hidden_requires_perm_salt_on_scan(self):
        """Hidden corpus must fail audit digest when TB3_PERM_SALT is omitted on scan."""
        tb3_dir = Path("/opt/verifier-fixtures/minclus/corpora")
        run_id = "run-tb3-nosalt"
        env = {"TB3_CORPUS_DIR": str(tb3_dir)}
        out = run_pipeline(run_id, "tb3-salt-shift", floor=0.5, env=env)
        rep = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_report(
            run_id,
            tb3_dir / "tb3-salt-shift",
            salt="shift-7",
        )
        assert rep["audit_digest"] != ref["audit_digest"]
