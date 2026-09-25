# Fixture catalog

Public scenarios live under `/app/fixtures/scenarios/`. Each file describes one workflow replay; field meanings follow the contract docs under `/app/docs/`.

`10-chained-trap.json` combines pinned routing, semver gate rejection, non-consecutive duplicate skip, ack delivery order, and server heartbeat offsets in one replay.

Verifier-only edge cases ship under `/opt/verifier-fixtures/scenarios/` and are not part of the agent image build context.
