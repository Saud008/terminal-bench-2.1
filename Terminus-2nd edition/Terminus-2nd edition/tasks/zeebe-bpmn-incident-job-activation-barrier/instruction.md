Activation barrier playfield playtest

Build the activation barrier playfield playtest, an offline tactics playtest planner for readiness sequencing and sealed activation-atlas win conditions on the working baseline under `/app`. The planner loads scenario playfield packs, applies marker-persistence traps, attached-element ordering gates, process-clock deadline fences, overlay-merge shelves, and idempotent replay dedup scoring, then seals an `export` playtest atlas when the activation-sequence win condition is met. This is a games activation-barrier playfield playtest and sealed-atlas workflow. It is not a software-engineering service repair, debugging task, system-administration ops desk, machine-learning eval lab, or data-processing pipeline.

`actplay` is available at `/usr/local/bin/actplay`.

```text
actplay export --scenario PATH --output PATH
```

`export` admits one scenario pack (bundled packs under `/app/fixtures/scenarios/`), materializes playfield staging at `/app/state/incident-snapshot.json`, and seals activation-atlas JSON at `--output` only from that staged snapshot. Default sealed atlas for merged playtest runs is `/app/output/job-activation-export.json`.

Win-condition contracts under `/app/docs/`:

- `incident-barrier.md` — marker-persistence trap timing and barrier labels
- `boundary-ordering.md` — attached-element ordering gates
- `job-deadline-clock.md` — process-clock deadline fences
- `variable-merge.md` — overlay-merge shelves and protected output-mapping sources
- `replay-dedup.md` — idempotent replay dedup scoring
- `staging-snapshot.md` — staging snapshot fields before sealed emit
- `export-schema.md` — sealed atlas field order
- `cli-errors.md` — refusal exit codes
- `fixture-catalog.md` — bundled playfield pack inventory

Hidden verifier packs may appear under `/opt/verifier-fixtures/actplay`. `/app/docs/`, `/app/fixtures/`, and `/app/config/` are read-only inputs that define the win-condition rules and fixture inventory. Offline only.
