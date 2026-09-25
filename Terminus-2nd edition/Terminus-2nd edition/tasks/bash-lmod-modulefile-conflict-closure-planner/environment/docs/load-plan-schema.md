# Load plan schema

Export writes JSON to the path given by --out with these fields:

- schema_version — integer, always 1
- catalog_digest — hex string copied from staging
- sequence — integer run ledger sequence from staging
- unload_sequence — JSON array of module names (lexicographically sorted)
- load_sequence — JSON array of module names (lexicographically sorted)
- path_mutations — JSON array of objects {var, op, value} in load order
- plan_digest — SHA256 of the canonical JSON body before adding plan_digest

Canonical JSON rules for plan_digest:
- Top-level keys sorted alphabetically
- unload_sequence and load_sequence sorted lexicographically
- path_mutations order preserved (load order)
- No extra whitespace; compact separators
