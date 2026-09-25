"""Harbor pytest entrypoint for oidcgov verification governance tests."""

from oidc_verdict_refmath import reference_governance_report, reference_transcript_digest  # noqa: F401

from test_oidc_govern_pipeline import *  # noqa: F403
from test_oidc_refmath_contracts import *  # noqa: F403
from test_oidc_tb3_hidden import *  # noqa: F403

# Literal artifact paths referenced in instruction.md (post-create audit cross-check).
AUDIT_COVERED_PATHS = (
    "/app/output/verification-governance-report.json",
    "/app/state/hydrate-revision.json",
    "/app/state/jwks-cache-snapshot.json",
    "/app/state/transcript-vault.json",
    "/app/state/verification-decisions.json",
)
