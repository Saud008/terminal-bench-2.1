Milestone 2 adds **dependency ordering and cycle detection** on parsed quadlet units. `quadlet-resolver order` must emit dependency-first unit order JSON or exit `2` with a `cycle:` stderr line per `/app/docs/dag-contract.md`.

Repair `/app/lib/dag.sh` while keeping milestone 1 parse behavior. Do not edit `/app/docs/` or `/app/fixtures/`.

```text
quadlet-resolver order --tree /app/fixtures/stack --out /app/output/order.json
```
