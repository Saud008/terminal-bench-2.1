# cronctl CLI

cronctl load --seed NAME --scenario SCENARIO
  Resolve SCENARIO.json using the fixture-root precedence below, then write /app/state/replay-snapshot.json.

cronctl replay --seed NAME --scenario SCENARIO
  Simulate the scenario window using the fake clock. TB3_CLOCK_START (RFC3339) overrides the fake-clock start for the tick loop (planned fire expansion and event offsets stay anchored to the scenario `window_start`; fires whose at_ms fall at or before the overridden clock start are skipped). TB3_TICK_MS sets tick duration in milliseconds (falls back to config tick_ms when unset or non-positive). Each tick must apply every planned fire whose at_ms falls in (previous_tick_ms, current_tick_ms], including fires that land exactly on the first tick. Event at_ms values are offsets from scenario window_start and use the same inclusive tick window.

cronctl export --seed NAME --scenario SCENARIO --output PATH
  Write ledger JSON to PATH using persisted SQLite rows and the staging snapshot.

## Fixture root precedence

1. If TB3_FIXTURE_DIR is set to an absolute directory, that directory is the sole scenario root (`$TB3_FIXTURE_DIR/SCENARIO.json`).
2. Otherwise use `/app/fixtures/scenarios/SCENARIO.json`.

Hidden verifier packs may mount under `/opt/verifier-fixtures/gocron/scenarios`. That path is not an automatic fallback; load/replay read it only when TB3_FIXTURE_DIR points there.
