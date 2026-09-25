# Outcome guard (stage 5b)

After `outcome.sh` writes `/app/work/replay.outcome.json` and before `export.sh` reads it, `outcome_guard.sh` validates snapshot invariants.

| Check | Requirement |
|-------|-------------|
| `version` | Must be `1` |
| Top-level keys | Only `version`, `stack`, `user`, `exit_code`, `phases`, `environment`, `audit_path` |
| `phases` order | Execution order (`auth` → `account` → `password` → `session`), never alphabetically sorted |
| `exit_code` | Non-zero when any phase `status` is `fail`; zero when all phases succeeded |

Guard failures abort export with non-zero exit. The CLI must still exit with the replay `exit_code` from execution — do not overwrite `PAMREPLAY_EXIT_CODE` in `outcome.sh` (see `/app/bin/pamreplay`).
