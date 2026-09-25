# Restore fixture catalog

| Restore file | Tables | Exercises |
|--------------|--------|-----------|
| `core-filter.v4` | filter | Policy counters, filter-only commit |
| `mangle-mark.v4` | mangle, nat | Mark set in mangle, DNAT mark match in nat |
| `triple-order.v4` | mangle, nat, filter | Full commit order + conntrack rules |
| `counter-heavy.v4` | filter, nat | Rule and policy counter preservation |
| `ctstate-mix.v4` | mangle, filter | Conntrack rule order across chains |
| `nat-only-deps.v4` | mangle, nat | Multiple marks; partial NAT activation |

Seeds are listed in `/app/fixtures/seeds.json`. Verifier uses every `(restore, seed)` pair in the catalog table.
