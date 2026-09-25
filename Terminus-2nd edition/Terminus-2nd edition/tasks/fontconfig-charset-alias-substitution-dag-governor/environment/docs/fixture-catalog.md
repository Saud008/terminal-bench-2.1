# Fixture catalog

All scenarios live under `/app/fixtures/configs/`. Fragments for inject tests live under `/app/fixtures/fragments/`.

| Config | Charset query | Family | Notes |
|--------|---------------|--------|-------|
| `base.conf` | `ISO8859-1:1987` | `serif` | Latin-1 serif substitution baseline |
| `base.conf` | `ISO8859-2:1987` | `sans` | Latin-2 sans substitution baseline |
| `revision.conf` | `ISO8859-1:1998` | `mono` | Revised Latin-1 mono stack |
| `revision.conf` | `ISO8859-1:1987` | `mono` | Original Latin-1 mono stack |
| `encoding-hop.conf` | `ISO8859-4:1988` | `serif` | Baltic serif stack |
| `reject-outline.conf` | `ASCII:1963` | `sans` | ASCII sans with outline policy |
| `overlay.conf` | *(check only)* | — | Standalone alias graph for `check` |
| `regression.conf` | `UNICODE:2024` | `serif` | Multi-hop alias and combined policies |

Inject fragments (merged at test time):

| Fragment | Base config | Purpose |
|----------|-------------|---------|
| `fragments/cycle-closer.conf` | `configs/base.conf` | Injected alias graph for `check` |
| `fragments/encoding-override.conf` | `configs/base.conf` | Injected charset hop overlay |
| `fragments/prefer-swap.conf` | `configs/base.conf` | Injected substitute overlay |

Seeds in `catalog.json` select export filename suffixes for multi-seed runs.
