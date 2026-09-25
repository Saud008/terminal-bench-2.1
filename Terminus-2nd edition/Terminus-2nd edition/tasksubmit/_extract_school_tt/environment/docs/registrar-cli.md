# CLI surface

Binary path: /app/bin/ttalloc

Fixed verb order for a full run:

1. load-roster --scenario NAME [--fixture-dir PATH]
2. materialize-graph --scenario NAME
3. allocate-slots --scenario NAME
4. publish-atlas --scenario NAME

State paths:

- /app/state/active-roster.json
- /app/state/scenario-active.json
- /app/state/constraint-graph.json
- /app/state/allocation-pass.json
- /app/work/allocate-log.json
- /app/output/timetable-atlas.json
- /app/output/conflict-report.json
