# Atlas ops workflow

Host-local glyph atlas bleed session control plane (atlasd / atlaspack).

## Ops pass order

1. Admit catalog JSON and sprite sheet files for one pack set and seed.
2. Apply padding, edge-bleed replication, rotation shelf, seed-scale, and oversized admission gates.
3. Stage packed layout in memory (no remote CDN publish).
4. Seal PNG atlas and checksum manifest exports only after gates pass.
5. Optional probe audits sealed atlas UV samples for one glyph frame.

## Normative contracts

- `/app/docs/atlas-contract.md` — pad-bleed, UV, rotation, duplicate frames, seed scale, size limit
- `/app/docs/manifest-schema.md` — sealed manifest fields and checksum
- `/app/docs/exit-codes.md` — pack and probe exit codes
- `/app/docs/atlas-runtime-paths.md` — fixtures, outputs, rebuild path
