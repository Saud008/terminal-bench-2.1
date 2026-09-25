# Procmail delivery simulator

Offline Bash tool that replays mbox fixtures through a procmailrc tree. Contracts live under `/app/docs/`.

## Commands

- `procmail-sim simulate --suite DIR [--snapshot FILE]` — stage delivery snapshot JSON
- `procmail-sim audit --snapshot FILE --output FILE` — emit audit report from snapshot only

## Layout

- `/app/lib/procmail-sim/` — simulator modules (agent repair target)
- `/app/fixtures/suites/` — bundled mbox + rc scenarios
- `/app/state/delivery-snapshot.json` — default snapshot path
- `/app/output/procmail-audit.json` — default audit export
