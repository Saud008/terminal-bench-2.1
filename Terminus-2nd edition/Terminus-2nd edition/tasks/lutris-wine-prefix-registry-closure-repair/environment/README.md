# Lutris prefix registry resolver

Repair `/app/lib/*.sh` so `lutris-resolve resolve` matches `/app/docs/resolve-contract.md`.

```bash
bash /app/scripts/reset-state.sh
lutris-resolve resolve \
  --registry-dir /app/fixtures/registry/001-transitive-runner \
  --root-slug frontier-rpg \
  --config /app/config/resolve.json \
  --output /app/output/resolve.json
```

Contracts: `/app/docs/registry-format.md`, `/app/docs/resolve-output-schema.md`.
