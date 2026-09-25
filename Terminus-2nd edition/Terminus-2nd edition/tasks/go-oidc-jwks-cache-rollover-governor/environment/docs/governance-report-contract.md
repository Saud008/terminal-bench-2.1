# Governance report emit

verification-governance-report.json fields: scenario, decision_count, decisions[], report_digest.

Each decision entry includes token_id, verdict (accept or reject), and reason_code describing the verification outcome.

Decisions sorted by token_id ascending.

emit-report requires hydrate_revision > 0.

report_digest is SHA-256 hex of compact JSON with keys decision_count, decisions, scenario.

## Official reason_code vocabulary

Pytest and independent reference math compare reason_code exactly. Use only the values in this table.

| reason_code | verdict | when emitted |
|-------------|---------|--------------|
| active_key | accept | Token kid matches an active key and cache max-age is fresh |
| grace_key | accept | Token kid matches a retired key and signature_epoch is within the inclusive grace window |
| key_revoked | reject | Token kid appears in the revoked set from any timeline event |
| key_retired | reject | Token kid matches a retired key but signature_epoch is outside the grace window |
| kid_unknown | reject | Token kid matches neither active nor retired keys after case-insensitive lookup |
| issuer_mismatch | reject | Token iss does not match policy issuer per issuer-audience-contract.md |
| audience_mismatch | reject | Token aud list fails policy audience binding per issuer-audience-contract.md |
| cache_stale | reject | Active key match but signature_epoch is older than cache_max_age_sec allows |
