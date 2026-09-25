# Runway snapshot contract

snapshot-runway writes runway-snapshot.json with runway_digest, nodes, and edges.

Every rights row must have a rights_contract edge linking program_id to contract_id in edges array.

Fingerprint is sha256 of seed concatenated with sorted program_id bytes.
