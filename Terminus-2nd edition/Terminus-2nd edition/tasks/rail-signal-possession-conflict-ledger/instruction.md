Yard possession conflict playtest

Build the yard possession conflict playtest, an offline track-block tactics playtest planner for possession and reservation conflict sealing on the working baseline under `/app`. The planner loads rail scenario packs, applies seeded protected-zone reachability scoring, audits half-open possession windows and signal-aspect traps, counts crisis-override suppressions, and seals `emit-conflicts` playtest exports when the conflict-ledger win condition is met. This is a games yard-block playtest and possession-conflict sealing workflow: keep protected-zone adjacency, half-open window invariants, signal matching, override precedence, zone-salt ordering, load_generation sequencing, staged playfield snapshots, and sealed conflict-ledger exports aligned. It is not a generic Rust CLI engineering, interlocking library rebuild, debugging, security admission, data-processing pipeline, or CI tooling exercise.

railpos is available at `/app/bin/railpos`. Subcommands and flags are cataloged under `/app/docs/`:

  compile-trackgraph
  emit-conflicts

`compile-trackgraph --seed S --scenario NAME` loads one scenario from `/app/fixtures/scenarios/`, writes the seed-scoped playfield staging snapshot at `/app/var/rail/trackgraph.snapshot`, and binds `/app/var/rail/authority.ticket`.

`emit-conflicts --seed S --scenario NAME --output PATH` seals conflict-ledger playtest JSON at the caller-provided `--output` path under `/app/output/` only from those on-disk staged playfield witnesses. When staged trackgraph or authority artifacts are missing or do not match the requested seed and scenario, emit-conflicts leaves `--output` unpublished.

Reachability, half-open windows, signal matching, override precedence, zone-salt ordering, and load_generation sequencing follow the contracts under `/app/docs/`. Bundled scenario packs and seeds live under `/app/fixtures/`. The decoy aspect helper stays outside the compile-trackgraph and emit-conflicts playtest hot path. Do not modify `/app/docs/`, `/app/fixtures/`, or `/app/config/`. Offline only.
