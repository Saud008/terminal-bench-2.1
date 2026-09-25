# Staging snapshot schema

gclint-staging.json contains run_id, stages array, jobs array, rules_fingerprint, staging_digest. Each job record includes name, stage, when, active, needs, duplicate, artifacts.paths. staging_digest hashes run_id, jobs name stage active, and rules_fingerprint.
