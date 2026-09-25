The `cdcctl` CLI at `/app/cmd/cdcctl` rolls binary fixtures through content-defined chunking, builds a merkle root over chunk hashes, and can resume interrupted rolls via checkpoint files. Code under `/app/internal/` must satisfy `/app/docs/roll-contract.md`, `/app/docs/merkle-tree.md`, and `/app/docs/fixture-catalog.md`.

For every fixture in `/app/fixtures/binaries/` and seed in `/app/config/seeds.json`, `cdcctl roll` must write JSON roll reports whose chunk boundaries follow the seed-derived CDC parameters, whose merkle roots match odd-leaf duplication rules, whose checkpoint files preserve rolling-window bytes and resume offsets, and whose `--resume` and `--max-chunks` flags continue rolls without duplicating or skipping bytes.

```text
cdcctl roll --input PATH --seed SEED [--output PATH] [--checkpoint PATH] [--resume] [--max-chunks N]
```
