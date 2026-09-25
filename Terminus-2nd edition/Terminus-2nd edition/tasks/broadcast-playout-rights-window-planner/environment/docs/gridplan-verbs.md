# CLI surface

Binary path: /app/bin/gridplan

Fixed verb order for a full run:

1. import-grid --scenario NAME [--fixture-dir PATH]
2. snapshot-runway --scenario NAME
3. compile-windows --scenario NAME
4. syndicate-plan --scenario NAME

State paths:

- /app/state/active-grid.json
- /app/state/scenario-active.json
- /app/state/runway-snapshot.json
- /app/state/compile-epoch.json
- /app/state/syndication-plan.db
- /app/work/window-compile-log.json
- /app/output/syndication-plan.json
- /app/output/conflict-report.json
