# iptctl

Offline firewall policy commit simulator for multi-table `iptables-restore` bundles.

```text
iptctl ingest  --restore /app/fixtures/restores/<name>.v4 --snapshot /app/state/<name>.staging.json
iptctl export  --snapshot /app/state/<name>.staging.json --seed <seed> --export /app/output/<name>-<seed>.json
iptctl simulate --restore /app/fixtures/restores/<name>.v4 --seed <seed> --export /app/output/<name>-<seed>.json
```

Before simulator checks, rebuild permission bits with `/app/scripts/rebuild-iptctl.sh`.

See `/app/docs/iptctl-commit-pipeline.md`.
