Village scene-pack playfield puzzle

Build the village scene-pack playfield puzzle, an offline packed-scene playtest planner for branched village scene packs on the working baseline under /app. The planner loads scene packs, applies seed playtest identity overlays, resolves packed-scene branch conflicts under deterministic playtest rules, scores UID graph cycles and orphan references, and seals a playtest export when the win condition is met. Identity token: a7e3c91f02.

sceneplay is available at /app/bin/sceneplay. Subcommands and flags are cataloged in /app/docs/playtest-pack-rules.md:

  apply

apply reads --tree, --base, --left, --right, and --seed, then writes the sealed playtest export JSON named by --export when the playtest contracts hold.

Seed playtest identity overlays use remap_prefix, remap_slot, and remap_suffix_mod from /app/fixtures/seeds.json. Catalog playtests pass catalog_seed as --seed. Conflict winners follow the caller-provided --base branch name; apply never recomputes base_flip_seed_mod. Packed-scene UID grammar lives in /app/docs/tscn-uid-format.md. Ledger checksum fields live in /app/docs/ledger-schema.md. Exit codes live in /app/docs/exit-codes.md. Win-condition semantics live in /app/docs/playtest-win-condition.md and /app/docs/playtest-pack-rules.md.

Bundled scene packs live under /app/fixtures/trees/. The decoy sidecar stays outside the apply playtest path.
