# Fixture catalog

Input fixtures live under `/app/fixtures/inputs/`.

| File | Exercises |
|------|-----------|
| `001-basic.hosts` | Plain hostname lowercasing and lexicographic output order |
| `002-hashed.hosts` | `\|1\|salt\|hash` field preservation and hashed sort keys |
| `003-revoked.hosts` | `@revoked` marker retention and non-revoked merge preference |
| `004-port-bracket.hosts` | `[host]:port` bracket normalization and multi-token sorting |
| `005-duplicates.hosts` | Duplicate hashed lines merged with comment tie-break |
| `006-mixed.hosts` | Plain + hashed + `@cert-authority` + revoked + bracket combinations |
