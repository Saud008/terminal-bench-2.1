# CLI surface

Binary: `/app/bin/platclosectl`

Verbs:

- `hydrate-plates --scenario <id>`
- `bind-residuals --scenario <id>`
- `seal-closure --scenario <id> [--output <path>]`

Exit codes: `2` for usage or missing required flags; `1` for laboratory failures including
seal without a prior bind pass; `0` on success. Missing verb prints usage mentioning all
three verbs on stderr.
