# PAM environment contract

Modules whose basename starts with `pam_env` declare environment assignments through `args` (`KEY=VALUE`).

## Initial state

Replay starts with an empty export `environment` object. The `--user` argument is passed to stub modules as `PAM_USER` at execution time only; it does **not** automatically add `USER`, `HOME`, or any other key to the export JSON. Only `pam_env` module `args` may populate the export `environment`.

Rules:

1. During **auth**, `pam_env` modules may run, but assignments are **pending** until the auth phase completes successfully.
2. If auth fails, pending auth-phase env assignments are **discarded** (never visible in the export `environment` object).
3. During **account** and later phases, `pam_env` assignments commit immediately when the module succeeds.
4. On stack failure after env was committed, **rollback** restores the pre-replay environment snapshot before audit export.

The export `environment` object must reflect only committed variables after rollback.
