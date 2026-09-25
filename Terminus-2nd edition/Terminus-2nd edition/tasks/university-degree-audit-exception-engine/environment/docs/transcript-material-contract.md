# Transcript materialization contract

materialize-transcript writes /app/state/transcript-material.json with keys:

- scenario
- engine (degaudit)
- material_fingerprint (sha256 hex)
- course_count
- enrollment_count

material_fingerprint covers course_code values sorted ascending joined by pipe, then catalog_seed.
