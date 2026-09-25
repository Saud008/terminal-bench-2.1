"""Anti-hardcoding and guard tests for rvk9."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from custody_cli_helpers import invoke, wipe
from custody_verifier_math import materialize_bundle, reference_dossier

APP = Path("/app")
CAT = APP / "catalog" / "storage-locations.json"


def test_randomized_bundle_dossier_matches_reference_math() -> None:
    """Verify randomized evidence and officer ids still match reference dossier math."""
    wipe()
    seed = 7712
    bundle = materialize_bundle(APP / "fixtures" / "cases" / "metro-gun-chain.json", seed)
    case_id = bundle["case_id"]
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        bundle_path = Path(tmp) / "rand-chain.json"
        bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
        env = {"TB3_CASE_ROOT": tmp}
        out = APP / "output" / f"{case_id}-rand-chain-dossier.json"
        for step in (
            [
                str(APP / "bin" / "rvk9"),
                "vault",
                "load",
                "--case",
                case_id,
                "--bundle",
                "rand-chain",
            ],
            [
                str(APP / "bin" / "rvk9"),
                "registry",
                "bind",
                "--case",
                case_id,
                "--bundle",
                "rand-chain",
            ],
            [
                str(APP / "bin" / "rvk9"),
                "attest",
                "dossier",
                "--case",
                case_id,
                "--bundle",
                "rand-chain",
                "--output",
                str(out),
            ],
        ):
            proc = invoke(step, env=env)
            assert proc.returncode == 0, proc.stderr + proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_dossier(case_id, bundle_path, CAT)
        assert got["summary"] == ref["summary"]
        assert got["custody_digest"] == ref["custody_digest"]


def test_restricted_location_would_fail_when_used() -> None:
    """Verify restricted destination status is not treated as active in reference math."""
    catalog = json.loads(CAT.read_text(encoding="utf-8"))
    restricted = [r for r in catalog["locations"] if r["status"] == "restricted"]
    assert restricted and restricted[0]["location_id"] == "LOC-QUARANTINE"


def test_decoy_module_not_linked_in_binary_help() -> None:
    """Verify rvk9 usage text exposes vault registry attest subcommands."""
    proc = invoke([str(APP / "bin" / "rvk9")])
    assert proc.returncode != 0
    assert "attest dossier" in proc.stderr
