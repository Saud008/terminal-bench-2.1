Milestone 3 adds **systemd unit emission**. `quadlet-resolver render` must write `.service` files per `/app/docs/emit-contract.md` after successful acyclic ordering.

Repair `/app/lib/emit.sh`. Prior milestones must keep working. Do not edit `/app/docs/` or `/app/fixtures/`.

```text
quadlet-resolver render --tree /app/fixtures/stack --out /app/output/units
```
