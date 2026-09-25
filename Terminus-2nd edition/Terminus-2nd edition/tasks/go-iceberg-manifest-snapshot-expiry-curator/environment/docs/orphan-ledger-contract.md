# Orphan ledger contract

Path: /app/output/orphan-ledger.jsonl

Each non-empty line is one compact JSON object with exactly two fields in this order: path then kind.

kind is always the literal lowercase ASCII string data. No other kind value is accepted.

path is the data_file path string for an orphaned file.

Orphans are data_file paths referenced by non-deleted manifest entries that are not reachable from the current snapshot manifest root per manifest-reach-contract.md. Manifest entries with status deleted are excluded from the referenced set.

Rows sort by path ascending using lexicographic string order.

Each line uses compact JSON (no insignificant whitespace) and ends with a single newline character U+000A. When the ledger has at least one row, the file ends with a trailing newline after the last row. An empty ledger is a zero-byte file.

Republish byte identity requirements appear in stable-republish-contract.md.
