# Task idea — haproxy-sticktable-session-governor

**Status:** Implemented and packed  
**Milestone:** non-milestone

## Title

haproxy-sticktable-session-governor

## Language

Go primary with Bash harness and Python verifier reference

## Category and subcategories

- category: `data-processing`
- subcategories: `[]`

## Target difficulty

Hard (not confirmed by frontier agent runs)

## Planned interacting bugs/behaviors (6)

1. table/seed — ignores seed_rows
2. stick/key — uses IP key when cookie present
3. expire/ttl — expired rows still match
4. pick/server — always picks servers[0] on miss
5. staging/snapshot — empty picks array
6. emit/report — re-reads scenario JSON instead of staging

## Why not one shallow patch

Cookie preference depends on seeded table rows and expiry.Fixing only emit still fails empty staging.Fixing only pick still fails cookie trap and expiry suite.Parametrized single module golden patch tests require all six modules.

## Likely frontier-agent failure modes

- Patch only emit or staging and pass 001 while failing hidden trap
- Fix cookie key but leave seed empty
- Ignore expire_seq on seed rows
- Edit decoy policy/wrap.go instead of contract modules
- Hardcode picks_digest in emit

## Tests that force real implementation repair

26 pytest cases via subprocess sticktbl simulate/emit, reference parity, snapshot only emit, hidden 101 cookie IP trap, seed mutation, decoy wrap trap, parametrized single module insufficiency

## Anti-hardcoding strategy

Runtime scenario SHA pins, hidden scenario under /tests/verifier-fixtures/, reference_stick.py, broken baseline at /opt/verifier-broken-sticktbl/, golden under /tests/verifier-golden/

## Oracle strategy

solution/solve.sh copies six golden Go patches, rebuilds sticktbl, resets state

## What could make this trivial and how we avoid it

| Trivializer | Avoidance |
|-------------|-----------|
| One bug emit only | Six modules plus single patch tests |
| Oracle writes JSON | Subprocess CLI tests |
| Hidden cookie rules | Documented in stick-key-policy.md |
| Hardcoded digest | Reference plus seed mutation plus hidden trap |
