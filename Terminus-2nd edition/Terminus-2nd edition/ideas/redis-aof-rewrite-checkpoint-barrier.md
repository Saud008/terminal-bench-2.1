# Task idea — redis-aof-rewrite-checkpoint-barrier

**Status:** Implemented and packed  
**Generated:** 2026-07-01  
**Milestone:** non-milestone

---

## Title

**redis-aof-rewrite-checkpoint-barrier**

## Language

**Go** (primary), Bash harness, Python verifier reference

## Category and subcategories

- **category:** `data-processing`
- **subcategories:** `[]`

## Target difficulty

**Hard** (not confirmed by agent runs on this host — Docker Desktop failed to start during verify)

## One-line capability framing

Implement `aofreplay` Go modules so replay materializes `/app/state/aof-staging.json` from suite preamble plus AOF JSONL streams and publish reads only staging to emit `/app/output/aof-export-report.json`.

## Planned interacting bugs/behaviors (6)

| # | Module | Broken behavior | Required fix |
|---|--------|-----------------|--------------|
| 1 | `internal/preamble/load.go` | Ignores preamble keys | Seed `InitialKeys` and live `Keys` from preamble |
| 2 | `internal/ops/txn.go` | Applies set/del during MULTI before EXEC | Buffer until EXEC, record history on apply |
| 3 | `internal/barrier/checkpoint.go` | Wrong barrier seq and `Within` logic | `max_seq = checkpoint seq`; include `seq <= barrier` |
| 4 | `internal/store/kv.go` | DEL is a no-op | Delete keys from live store |
| 5 | `internal/ledger/staging.go` | Writes empty `keys` map | Persist full filtered manifest in snapshot |
| 6 | `internal/export/publish.go` | Re-reads replay file | Digest staging keys only (`k=v` sorted) |

## Why not solvable by one shallow patch

Checkpoint filtering depends on transaction history and preamble baseline. Fixing only `publish` still fails staging and barrier suites. Fixing only `txn` still fails preamble seeding, empty staging, and snapshot-only publish. Parametrized single-module golden patch tests require all six modules.

## Likely frontier-agent failure modes

- Patch only `publish` or `staging` and pass suite 001 while failing 002/003/hidden trap
- Fix MULTI/EXEC but leave checkpoint `seq+1` off-by-one
- Treat post-checkpoint DEL as removing pre-barrier keys (wrong manifest model)
- Edit decoy `internal/replay/wrap.go` instead of the six contract modules
- Hardcode manifest digests instead of deriving from filtered keys

## Tests that force real implementation repair

23 pytest cases via subprocess CLI (`aofreplay replay` / `publish`):

- Reference parity on public suites 001–003 (snapshot + publish)
- `exported_at_seq` contract (checkpoint vs last-seq)
- Publish succeeds after suite fixtures removed (snapshot-only)
- Hidden `101-multi-checkpoint-trap` (post-barrier del must not erase `a`)
- Parametrized single-module golden patch insufficiency (all 6 modules)
- Decoy wrap-only patch trap
- `VERIFIER_SEED` mutation suite

## Anti-hardcoding strategy

- Public fixture SHA-256 pins in tests
- Hidden suite only under `/tests/verifier-fixtures/`
- Independent `reference_aof.py` (not in agent image logic)
- Broken baseline at `/opt/verifier-broken-aofreplay/` for patch tests
- Golden patches only under `/tests/verifier-golden/`

## Oracle strategy

`solution/solve.sh` copies six golden `.go` patches, rebuilds `/usr/local/bin/aofreplay`, resets state.

## What could make this trivial and how we avoid it

| Trivializer | Avoidance |
|-------------|-----------|
| One-bug publish-only fix | Six independent broken modules + single-patch tests |
| Oracle writes JSON directly | Tests invoke CLI subprocesses |
| Hidden barrier rules | Documented in `/app/docs/checkpoint-barrier.md` |
| Hardcoded export output | Reference + seed mutation + hidden trap |
| Editing pre-wired `engine.go` only | Decoy `wrap.go`; real bugs in six modules |

## Implementation path

`tasks/redis-aof-rewrite-checkpoint-barrier/`  
Zip: `tasksubmit/redis-aof-rewrite-checkpoint-barrier.zip`
