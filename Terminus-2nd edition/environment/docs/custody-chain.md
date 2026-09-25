# Custody chain

Prepare and commit share a custody journal that seals successful releases for governance export.

## Dual-phase CLI

| Command | Role |
|---------|------|
| prepare | Ingest scenario, bump epoch, write staging, init ledger and session, clear and create the custody journal, write /app/state/prepare-seal.json |
| commit | Read the prepare seal, process release rows, append custody receipts, emit export |
| reconcile | Runs prepare then commit for the same scenario and seed |

Commit must not re-ingest the scenario spool. Commit reads scenario label, seed, and requests path from the prepare seal at /app/state/prepare-seal.json

## prepare-seal.json

Written only by prepare:

| Field | Meaning |
|-------|---------|
| scenario | Scenario label (directory basename, never a full absolute path) |
| seed | Seed argument from prepare |
| requests_path | Absolute path to the scenario requests.json used at prepare time |
| release_epoch | Epoch value after the prepare bump |
| policy_digest | Staging policy_digest at prepare time |
| prepare_fingerprint | First twenty-four hex characters of sha256(scenario + ":" + seed + ":" + policy_digest) |

prepare_fingerprint must use the scenario basename even when reconcile or prepare was invoked with an absolute scenario directory path.

## Custody journal

Path /app/state/custody-journal.jsonl

Prepare truncates this file to empty. Each successful release (status released, after ledger sequence assignment) appends one JSON object line:

| Field | Meaning |
|-------|---------|
| sequence | Ledger sequence assigned to the release |
| quarantine_id | Released quarantine id |
| class | Request class (spam or virus) |
| receipt | Class-dependent receipt hex (sixteen characters) |

Duplicate skips and failed releases must not append journal lines.

### Receipt formula

For class spam:

sha256(seed + "|" + quarantine_id + "|" + sequence + "|" + class) hex, first sixteen characters.

For class virus:

sha256(quarantine_id + "|" + seed + "|" + sequence + "|" + class) hex, first sixteen characters.

Virus swaps seed and quarantine_id relative to spam. Using the spam formula for virus receipts is incorrect.

## custody_root

Export field custody_root is the sha256 hex digest of journal receipt values joined by a single newline in journal file order (sequence ascending as appended). When the journal has no lines, custody_root is the empty string.

## Export coupling

Export must copy prepare_fingerprint from /app/state/prepare-seal.json for the current prepare. Do not recompute the fingerprint at export time from live arguments alone.

Export must publish custody_root computed from the journal after all release attempts for this commit.
