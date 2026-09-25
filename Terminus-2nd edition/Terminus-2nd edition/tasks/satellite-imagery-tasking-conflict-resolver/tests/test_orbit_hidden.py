"""Hidden trap tests for satellite resolve — /opt/verifier-fixtures/satimg packs."""

from __future__ import annotations

import sys

sys.path.insert(0, '/app/environment')

import json
import os
from pathlib import Path

from verifier_contracts.satimg_contract_math import (
    HIDDEN_DIGEST_TRAP,
    HIDDEN_PADDING_TRAP,
    assert_manifest_matches,
    reference_from_scenario,
    run_resolve,
)

VERIFIER_FIXTURES = "/opt/verifier-fixtures/satimg"
OUT = "/app/output/"


def _hidden_root() -> Path:
    return Path(os.environ.get("SAT_FIXTURE_ROOT", VERIFIER_FIXTURES))


def test_satimg7_tb3_pad_trap():
    """TB3 padding-overlap-trap under /opt/verifier-fixtures/satimg enforces setup padding."""
    os.environ["SAT_FIXTURE_ROOT"] = str(_hidden_root())
    assert VERIFIER_FIXTURES in HIDDEN_PADDING_TRAP
    try:
        out = run_resolve("padding-overlap-trap", "tb3-pad")
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_from_scenario("padding-overlap-trap", "tb3-pad")
        assert body["assignment_count"] == 1
        assert_manifest_matches(body, ref)
    finally:
        os.environ.pop("SAT_FIXTURE_ROOT", None)


def test_satimg7_tb3_digest_trap():
    """TB3 digest-preempt-trap under /opt/verifier-fixtures/satimg binds preemption_trace digest."""
    os.environ["SAT_FIXTURE_ROOT"] = VERIFIER_FIXTURES
    try:
        out = run_resolve("digest-preempt-trap", "tb3-dig")
        body = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_from_scenario("digest-preempt-trap", "tb3-dig")
        assert body["preemption_count"] == 1
        assert_manifest_matches(body, ref)
    finally:
        os.environ.pop("SAT_FIXTURE_ROOT", None)


def test_satimg7_tb3_fixture_root():
    """SAT_FIXTURE_ROOT redirect loads /opt/verifier-fixtures/satimg scenario packs."""
    os.environ["SAT_FIXTURE_ROOT"] = HIDDEN_DIGEST_TRAP.rsplit("/", 1)[0]
    try:
        body = json.loads(run_resolve("digest-preempt-trap", "tb3-root").read_text())
        assert body["scenario_id"] == "digest-preempt-trap"
    finally:
        os.environ.pop("SAT_FIXTURE_ROOT", None)
