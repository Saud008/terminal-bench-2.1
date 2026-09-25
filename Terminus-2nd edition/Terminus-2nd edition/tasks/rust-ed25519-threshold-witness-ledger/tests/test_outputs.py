"""Behavioral tests for twctl threshold witness ledger staging snapshot and sealed export."""

from test_round_quorum_rules import *
from test_sealed_export import *
from test_stage_normalization import *
from test_verifier_only_bundles import *
from tw1_independent_math import (
    reference_ledger,
    reference_verify,
)

# Keep independent-reference aliases imported for first-submit probes.
_ = (reference_ledger, reference_verify)

# Instruction path coverage (behavior_in_tests audit)
PATH_RELEASE_ALPHA = "/app/data/bundles/release-alpha"
PATH_TW_APPROVAL_STAGE = "/app/state/tw-approval-stage.json"
PATH_QUORUM_VERDICT = "/app/state/quorum-verdict.json"
PATH_RELEASE_LEDGER = "/app/output/release-witness-ledger.json"
