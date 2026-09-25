# CLI surface

Binary path: `/app/bin/airclos`

Verbs, applied in order for a full closure run:

1. `bind-campaign --scenario SCENARIO [--fixture-dir DIR]`
2. `close-chronology --scenario SCENARIO`
3. `fold-closure --scenario SCENARIO`
4. `seal-atlas --scenario SCENARIO [--output PATH]`

Default fixture dir is `/app/fixtures`. Default atlas path is `/app/output/impact-closure-atlas.json`.

Sealed artifacts:

- `bind-campaign` writes `/app/state/campaign-binding.json`.
- `close-chronology` writes `/app/state/chronology-closure.json`.
- `fold-closure` writes `/app/state/closure-lattice.json` and bumps `/app/state/seal-epoch.json`.
- `seal-atlas` writes the atlas and requires `seal_epoch` greater than zero.

Unknown flags are errors. A missing `--scenario` is an error. Failures exit non-zero and write a human-readable message to stderr.
