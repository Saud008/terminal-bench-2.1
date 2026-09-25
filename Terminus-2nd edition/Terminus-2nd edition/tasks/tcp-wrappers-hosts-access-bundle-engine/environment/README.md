# hostsctl

TCP wrapper bundle merge and access decision tool.

Commands:

- `hostsctl merge --bundle /app/fixtures/bundles/office-edge --export /app/output/smoke-merged.json`
- `hostsctl decide --bundle /app/fixtures/bundles/office-edge --daemon sshd --ip 203.0.113.10 --export /app/output/smoke-decide.json`

See `/app/docs/merge-contract.md`, `/app/docs/decide-contract.md`, and `/app/docs/fixture-catalog.md`.

Bundle fixtures live under `/app/fixtures/bundles/`. Reset runtime state with `/app/scripts/reset-state.sh`.

`hostsctl` is on `PATH` at `/usr/local/bin/hostsctl`. Patch `/app/lib/` and validate with `bash -n` before rerunning.

Spot checks after fixes:

```bash
hostsctl decide --bundle /app/fixtures/bundles/wrap-join --daemon sshd --ip 198.51.100.50 --export /app/output/wrap-check.json
hostsctl merge --bundle /app/fixtures/bundles/office-edge --export /app/output/replay-prep.json
hostsctl replay --bundle /app/fixtures/bundles/office-edge --session /app/output/bad-session.json --export /app/output/replay-check.json
# bad-session.json: one row with decision "deny" for 203.0.113.10 / sshd — replay must exit 1
```
