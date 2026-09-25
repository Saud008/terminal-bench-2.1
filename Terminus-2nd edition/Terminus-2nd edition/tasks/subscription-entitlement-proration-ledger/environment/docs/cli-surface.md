# cli-surface.md

Entitlement trust-admission verbs for the invoice-seal control plane:

subledctl load-cycle --scenario SCENARIO [--fixture-dir DIR]
subledctl reconcile-entitlements --scenario SCENARIO
subledctl publish-invoices --scenario SCENARIO [--output PATH]

Reconcile evaluates authenticity and admission gates, then stages the entitlement buffer. Publish seals a subscription invoice attestation and entitlement lineage rollup only after reconcile_pass is positive.
