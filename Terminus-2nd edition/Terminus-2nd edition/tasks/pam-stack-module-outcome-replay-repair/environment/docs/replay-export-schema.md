# Replay export schema

`pamreplay replay --export PATH` writes UTF-8 JSON:

```json
{
  "stack": "/app/fixtures/stacks/001-basic-login.json",
  "user": "alice",
  "exit_code": 0,
  "phases": [
    {
      "phase": "auth",
      "status": "ok",
      "modules_run": 1
    },
    {
      "phase": "account",
      "status": "ok",
      "modules_run": 2
    },
    {
      "phase": "session",
      "status": "ok",
      "modules_run": 1
    }
  ],
  "environment": {
    "ROLE": "login",
    "SHELL": "/bin/bash"
  },
  "audit_path": "/app/output/001-basic-login.audit.jsonl"
}
```

- `stack`: the stack path exactly as supplied on the command line via `--stack /absolute/path`; the literal argument value is recorded verbatim, with no normalization, symlink resolution, or relative-to-absolute rewriting.
- `user`: replay request username passed to stub modules as `PAM_USER`; it is **not** copied into the export `environment` object unless a `pam_env` module assigns it.
- `exit_code`: `0` on success, `1` on PAM failure, `2` on parse or usage errors.
- `phases`: one object per phase **attempted** in contract order (skipped phases omitted).
- `environment`: committed variables from successful `pam_env` modules only, after any rollback. Replay begins with an empty object; do not pre-seed `USER`, `HOME`, or other keys from `--user`.
- `audit_path`: sibling audit JSONL path derived from `--export`.

Missing `--stack`, `--user`, or `--export`, or a missing stack file, must exit non-zero.
