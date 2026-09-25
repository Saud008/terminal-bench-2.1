# Task idea — bind-zone-serial-notify-governor

**Status:** Implemented and packed  
**Milestone:** non-milestone

## Title

bind-zone-serial-notify-governor

## Language

Go primary with Bash harness and Python verifier reference

## Category and subcategories

- category: `data-processing`
- subcategories: `[]`

## Target difficulty

Hard (not confirmed by frontier agent runs)

## Planned interacting bugs/behaviors (7)

1. baseline — ignores zone serial and records
2. soa/canonical — no zone name normalization
3. serial — naive uint32 compare breaks wrap
4. notify — wrong gate seq and Within logic
5. record — DEL is no-op
6. staging — empty targets in snapshot
7. emit — re-reads journal file instead of staging

## Why not one shallow patch

notify gate depends on journal history and baseline seeding.Fixing only emit still fails staging and gate suites.Fixing only serial still fails canonical zone and notify cutoff.Parametrized single module golden patch tests require all seven modules.

## Likely frontier-agent failure modes

- Patch only emit or staging and pass suite 001 while failing 002/003/hidden trap
- Fix notify gate but leave RFC serial wrap broken on suite 003
- Treat post gate DEL as removing pre gate owners from targets
- Edit decoy policy/wrap.go instead of contract modules
- Hardcode manifest digests

## Tests that force real implementation repair

27 pytest cases via subprocess zonenotify apply/emit, reference parity, snapshot only emit, hidden 101 multi gate trap, seed mutation, decoy wrap trap, parametrized single module insufficiency

## Anti-hardcoding strategy

Runtime fixture hash pins, hidden suite under /tests/verifier-fixtures/, reference_zone.py, broken baseline at /opt/verifier-broken-zonenotify/, golden patches under /tests/verifier-golden/

## Oracle strategy

solution/solve.sh copies seven golden Go patches, rebuilds zonenotify, resets state

## What could make this trivial and how we avoid it

| Trivializer | Avoidance |
|-------------|-----------|
| One bug emit only | Seven modules plus single patch tests |
| Oracle writes JSON | Subprocess CLI tests |
| Hidden gate rules | Documented in notify-gate-semantics.md |
| Hardcoded manifest | Reference plus seed mutation plus hidden trap |
