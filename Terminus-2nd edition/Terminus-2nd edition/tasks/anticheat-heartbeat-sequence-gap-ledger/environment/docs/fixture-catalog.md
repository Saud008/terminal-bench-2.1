# Fixture catalog

Public catalog: `/app/fixtures/catalog.json`

Hidden verifier fixtures are installed under `/opt/verifier-fixtures/` at image build:

| File | Role |
|------|------|
| `attest_hidden_linear.json` | Linear discontinuity + full in-grace repair under an unseen seed |
| `attest_hidden_wrap.json` | uint32 wrap continuity with zero breaches |

Procedural token and session mutations follow `VERIFIER_SEED` when the verifier harness sets it. Catalog scenarios describe bind/batch schedules; expected counters are derived from continuity policy, not hard-coded shortcuts.
