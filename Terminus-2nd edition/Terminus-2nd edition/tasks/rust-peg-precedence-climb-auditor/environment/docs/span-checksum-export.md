# Span checksum export

pestctl audit export writes /app/output/span-audit.json with grammar_id, ingest_seq from the rule graph, and spans ledger rows.

Each spans row lists kind, span start inclusive and end exclusive token indices, and recovered boolean.

The ledger must include every span node from the parse tree root walk plus every node listed in parse-tree recovered_nodes. Recovered error_recovery nodes on backtrack paths are mandatory ledger entries.

/app/output/span-checksum.txt is the lowercase hex SHA-256 of the compact JSON serialization of the audit file (serde_json default field order, no pretty printing).
