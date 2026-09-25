# Cadence decision-task replay

Offline Cadence-style workflow replay tool. Source lives under /app/internal; scenarios under /app/fixtures/scenarios.

Rebuild after edits:

go build -mod=readonly -o /usr/local/bin/cadence-replay ./cmd/cadence-replay

Run /app/scripts/reset-state.sh before local checks.
