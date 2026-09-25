# Platform rubric — blood-bank-crossmatch-release-ledger

**Task folder:** tasks/blood-bank-crossmatch-release-ledger/

Agent imports patient panels and donor units into /app/state/release.db via import-panels, +3
Agent scores ABO recipient rules when pairing patients to donor units, +3
Agent blocks Rh positive units for Rh negative patients without waiver rows, +3
Agent excludes units carrying antigens matching patient antibody screens, +3
Agent rejects units whose expires_at is before release_clock, +3
Agent records emergency waiver authorizer and reason on override releases, +3
Agent writes compatibility-matrix JSONL staging before seal-releases, +2
Agent increments screening_pass in /app/state/screening-pass.json on score-compatibility, +2
Agent blocks seal-releases until screening_pass is positive, +2
Agent publishes sorted release ledger at /app/output/release-ledger.json with ledger_digest, +2
Agent seals releases idempotently without duplicating ledger rows on repeat publish, +2
Agent rebuilds bbreleasectl via rebuild-bbreleasectl.sh before subprocess CLI checks, +2
Agent accepts Rh positive unit for Rh negative patient without override row, -3
Agent maps anti-D screen to wrong antigen token during exclusion, -3
Agent compares collected_at instead of expires_at for shelf-life rejection, -3
Agent drops waiver authorizer from sealed release audit rows, -3
Agent inserts duplicate ledger rows when seal-releases runs twice on same pass, -3
