# Asset criticality escalation

asset_criticality rows map asset_id to a base tier and escalation_ms timestamp.

Severity tiers ordered low, medium, high, critical.

When detected_ms is greater than or equal to escalation_ms, escalate exactly one tier from the configured base tier.
Escalation may reach critical.

Assets without a row use the default_severity_tier from correlator.json (low).
