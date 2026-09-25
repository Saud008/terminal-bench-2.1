# Fixture catalog

Snapshots live in `/app/fixtures/stacks/`. Replay each file below with `pulumi-dep-export order`.

| File | Exercises |
|------|-----------|
| `01-baseline.json` | Provider ref + explicit dependency chain |
| `02-parent-chain.json` | Implicit parent edges through VPC → subnet → instance |
| `03-depends-directed.json` | Directed `dependsOn` chain (role → lambda → log group) |
| `04-provider-ref.json` | Multiple providers; random provider before custom resource |
| `05-delete-before-replace.json` | Adjacent replace pair + dependent object |
| `06-component-nested.json` | Component wrapper keeps child depth; sibling alarm outside component |
| `07-merged.json` | Combined parent, provider, component, DBR, and dependency constraints |
| `08-tiebreak.json` | Parallel siblings after provider; snapshot index tie-break beats URN sort |

CLI example:

```text
pulumi-dep-export order --stack /app/fixtures/stacks/07-merged.json --output /app/output/merged-order.json
```
