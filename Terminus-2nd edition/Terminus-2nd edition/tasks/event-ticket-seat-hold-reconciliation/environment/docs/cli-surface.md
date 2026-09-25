# venuetixctl CLI surface

Binary path: /app/bin/venuetixctl

Fixed pipeline order for every scenario:

1. load-venue --scenario NAME [--fixture-dir PATH]
2. snapshot-holds --scenario NAME
3. reconcile-map --scenario NAME
4. publish-status --scenario NAME

Environment overrides:

- TB3_FIXTURE_DIR replaces default /app/fixtures
- TB3_EVENT_CLOCK replaces event_clock from scenario_meta
