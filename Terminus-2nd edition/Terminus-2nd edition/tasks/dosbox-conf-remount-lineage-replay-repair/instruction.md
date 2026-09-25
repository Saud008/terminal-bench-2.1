The `dosbox-plan` CLI at `/app/bin/dosbox-plan` reads DOSBox-style `.conf` fragments listed in each fixture manifest and writes a remount lineage JSON plan, but replay output and exit codes do not match `/app/docs/remount-contract.md`.

Repair the Bash libraries under `/app/lib/` so:

```text
/app/bin/dosbox-plan render --conf-dir PATH --profile NAME --config /app/config/plan.json --output PATH
```

writes JSON per `/app/docs/plan-output-schema.md`. Conf grammar and manifest layout are in `/app/docs/conf-format.md` and `/app/docs/fixture-catalog.md`.

Exit `0` on success. Exit `1` when the conf directory, manifest, or a listed conf file is missing. Exit `2` when a mount or `imgmount` command uses an invalid drive letter (errors recorded in output).

Use `/app/scripts/reset-state.sh` before local runs. Do not edit `/app/docs/`, `/app/fixtures/`, `/app/config/plan.json`, or files under `/tests/`.
