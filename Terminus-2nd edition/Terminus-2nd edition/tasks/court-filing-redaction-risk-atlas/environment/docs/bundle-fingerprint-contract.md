# Bundle fingerprint snapshot

Path: /app/state/bundle-fingerprint.json

Fields: engine, scenario, dockets, parties, pages, sealed_terms, policy, bundle_digest.

bundle_digest is SHA-256 hex of sorted JSON object with keys dockets, parties, pages, policy, scenario, sealed_terms sorted at root using compact separators.

Pages rerun in ascending page_num order during scan.
