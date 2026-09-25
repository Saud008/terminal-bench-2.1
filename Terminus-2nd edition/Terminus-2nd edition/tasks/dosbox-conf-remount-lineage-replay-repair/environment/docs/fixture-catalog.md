# Fixture catalog

Bundled under `/app/fixtures/confs/`. Each row is `fixture-id` → focus behavior.

| ID | Behavior |
|----|----------|
| `001-basic-mount` | Single autoexec mount |
| `002-config-precedence` | Config remap must apply before autoexec replay |
| `003-imgmount-remap` | Remap applies to imgmount drive and `D:` path prefix |
| `004-duplicate-stack` | Two mounts on same drive produce two lineage entries |
| `005-line-continuation` | Backslash continuation in mount path |
| `006-invalid-drive` | Non-letter drive exits 2 |
| `007-multi-file` | Multi-file manifest with cross-file config precedence |
| `008-interleaved-sections` | Config section appears after autoexec in file; global config-first still required |

Use `/app/scripts/reset-state.sh` before rendering. Output defaults to `/app/output/plan.json`.
