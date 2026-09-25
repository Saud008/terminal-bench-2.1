# SPIFFE pair capture snapshot

Path: /app/state/pair-capture.json

Fields: engine, scenario, left, right, capture_digest.

capture_digest is SHA-256 hex of compact JSON object with keys left, right, scenario in sorted key order at the root using compact separators.

Left must correspond to left.json and right to right.json from the scenario fixture pair.
