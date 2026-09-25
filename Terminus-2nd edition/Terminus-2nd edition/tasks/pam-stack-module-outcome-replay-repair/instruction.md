The pamreplay CLI under /app simulates Linux-PAM stack replay using stub modules in /app/stubs/ and stack definitions under /app/fixtures/stacks/. Its Bash libraries under /app/lib/ no longer honor the contracts in /app/docs/.

Repair pamreplay so every stack in /app/docs/fixture-catalog.md replays correctly. Replay is a multi-stage pipeline; module roles, artifacts, and ordering are defined under /app/docs/ (see /app/docs/outcome-snapshot.md, /app/docs/staging-contract.md, and related contract files). Patch /app/lib/ only.

Consult /app/docs/ for full requirements:

- **CLI exit code:** /app/bin/pamreplay — failed replays exit non-zero even when export succeeds.
- **Audit:** /app/docs/audit-format.md
- **Outcome snapshot:** /app/docs/outcome-snapshot.md — include version (1) and stack (absolute path to the stack JSON file); /app/docs/outcome-guard.md validates before export.
- **Export:** /app/docs/replay-export-schema.md — reads the validated outcome snapshot only; do not re-execute modules.

Do not edit /app/docs/, /app/fixtures/, /app/stubs/, or /tests/.
