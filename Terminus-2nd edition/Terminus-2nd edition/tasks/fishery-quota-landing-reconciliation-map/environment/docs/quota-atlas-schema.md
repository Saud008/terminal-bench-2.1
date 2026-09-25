# Quota atlas schema

Output path: caller-provided --dest under /app/output/ (absolute path required). Pytest may emit sample atlases such as /app/output/tok-subproc.json when exercising subprocess CLI invocation.

run_token on the atlas JSON equals the fqrctl --token argument for that emit pass.

species_rows sorted by species ascending. Each row: species, allocated_kg, landed_kg, remaining_kg, over_quota_kg rounded to two decimals.

landing_audit sorted by landing_id ascending mirroring JSONL accept flags.

summary includes accepted_rows and species_tracks.

atlas_fingerprint is sha256 hex of JSON with species_rows and landing_audit only.

publish-atlas sums live_weight_kg only for accepted JSONL landings when computing landed_kg per species.
