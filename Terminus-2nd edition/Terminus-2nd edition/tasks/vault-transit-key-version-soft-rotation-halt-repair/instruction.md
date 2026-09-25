The in-container `transit-mock` service loads transit key policies and serves a reduced Vault Transit HTTP API, but policy parsing, version-ledger deletes, batch encrypt version picks, convergent encrypt version selection, and soft rotation halt gating do not follow `/app/docs/transit-rotation.md`.

Repair these packages so behavior matches the contract and `/app/docs/http-api.md`:

- `/app/internal/policy/policy.go` — parse `min_decryption_version` from policy JSON and enforce it on decrypt
- `/app/internal/ledger/ledger.go` — honor `deletion_allowed` before mutating the ledger; pick the same latest active encrypt version for every batch item
- `/app/internal/encrypt/encrypt.go` — convergent encrypt uses the latest active version; soft halt retires versions for encrypt (still decryptable when above min decrypt)

Do not edit `/app/docs/` or `/app/fixtures/`.

After patching, rebuild and restart:

```bash
/app/scripts/verifier-rebuild.sh
/app/scripts/start-server.sh
```

Exercise the HTTP API against the running service. Responses include status codes plus version and halt headers as documented.
