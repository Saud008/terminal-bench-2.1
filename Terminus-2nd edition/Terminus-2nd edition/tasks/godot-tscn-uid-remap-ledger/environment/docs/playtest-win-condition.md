# Playtest win condition

`sceneplay apply` seals a playtest export when these win rules hold together:

1. Seed identity overlays from `/app/fixtures/seeds.json` are applied before branch resolution.
2. Packed-scene conflict winners follow the caller-provided `--base` branch name.
3. Directed PackedScene UID graphs report cycles when present; exit code is `2` when `uid_graph_ok` is false, and the export is still written.
4. Orphan UID references remaining after `delete_on_merge` omissions appear in `orphans`.
5. Ledger `content_sha256` values hash LF-normalized scene text.

Full field tables and formulas live in `/app/docs/playtest-pack-rules.md`, `/app/docs/tscn-uid-format.md`, `/app/docs/ledger-schema.md`, and `/app/docs/exit-codes.md`.
