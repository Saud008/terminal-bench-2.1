# pamreplay

Simulated Linux-PAM stack replay for login-style services. See `/app/docs/` for contracts.

```bash
pamreplay replay --stack /app/fixtures/stacks/001-basic-login.json \
  --user alice --export /app/output/001-basic-login.json
```

## Agent workflow

- Edit `/app/lib/*.sh` with normal shell tools (`sed`, heredocs, or your editor). **`apply_patch` is not available** in this environment.
- Do **not** override `PAMREPLAY_STACKS_ROOT` or `PAMREPLAY_APP_ROOT`; `pamreplay` resets them on each run.
- After each change, run **`bash /app/scripts/smoke-replay.sh`** for a fast sanity check instead of replaying every catalog stack in a loop.
- Full stack list and expected behaviors: `/app/docs/fixture-catalog.md`.
