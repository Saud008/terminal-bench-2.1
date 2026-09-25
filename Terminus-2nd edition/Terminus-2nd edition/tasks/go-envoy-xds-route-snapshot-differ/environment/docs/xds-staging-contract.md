# xDS staging snapshot

Path: /app/state/xds-staging.json

Fields: engine, scenario, left, right, staging_digest.

staging_digest is SHA-256 hex of compact JSON object with root keys left, right, scenario in that order. Nested snapshot fields keep schema field order from the xDS snapshot model, not recursive key sorting.

Left must correspond to left.json and right to right.json from the scenario fixture pair.
