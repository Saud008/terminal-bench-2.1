# wavehold — host-local fleet cutover hold-preview

Fleet cutover administrators run the host-local `wavehold` control plane to
preview whether mutation-wave commits would be held or admitted before a
graph-fleet cutover, then publish a sealed rollout atlas for downstream ops
diff. There is no remote graph-fleet cluster.

## Operator surface

```
wavehold scan    --wave <jsonl> --run-id <id>     # admit wave into run state
wavehold compile --run-id <id>                    # hold-preview gates + witness
wavehold publish --run-id <id> --output <path>    # sealed rollout atlas
```

- Run state: `/app/state/wavehold/runs/<id>/`
- Staged witness: `/app/state/wavehold/hold-witness.json`
- Default atlas: `/app/output/mutation-rollout-atlas.json`

## Paths

- `/app/bin/wavehold` — operator CLI
- `/app/config/wavehold.json` — hold policy
- `/app/fixtures/waves/*.jsonl` — public mutation waves
- `/app/docs/` — ops contracts (immutable)
- `/app/lib/meridian/decoy/` — unused wall-clock helper (must not affect outcomes)

This is a system-administration host-local fleet cutover control plane.
