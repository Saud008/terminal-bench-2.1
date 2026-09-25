# trust-evaluation-surface-contract.md

Independent reference entitlement math recomputes invoice and staging digests from admitted cycle manifests. Subprocess drives load-cycle, reconcile-entitlements, and publish-invoices against the host-local trust journal at /app/state/billing.db.

Hidden scenarios load from /opt/verifier-fixtures/subledctl when TB3_FIXTURE_DIR is set. TB3_PRORATION_BPS may adjust proration rounding on verifier-only cycles under the same authenticity gates.
