# intakectl command reference

Shelter kennel placement pipeline uses bind, weave, and seal subcommands only.

Binary path: /app/bin/intakectl

Fixed pipeline order for every run-id:

1. bind --registry sqlite --arrivals jsonl --run-id RUN --scenario NAME [--fixture-dir PATH]
2. weave --run-id RUN
3. seal --run-id RUN --output PATH

Environment overrides:

- TB3_FIXTURE_DIR replaces default /app/fixtures
- TB3_INTAKE_DATE replaces intake_date from scenario_meta during weave
