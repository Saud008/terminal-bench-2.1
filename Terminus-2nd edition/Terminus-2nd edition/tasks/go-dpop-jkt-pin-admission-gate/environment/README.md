# jktadmit

Offline DPoP (RFC 9449-style) jkt-pin admission gate.

- Binary: `/usr/local/bin/jktadmit` (mirrored at `/app/bin/jktadmit`)
- Config: `/app/config/jktadmit.json`
- Docs: `/app/docs/`
- Chainhead snapshot: `/app/state/chainhead.json`
- Sealed ledger: `/app/output/deny-ledger.json`

Run `bash /app/scripts/reset-state.sh` to clear state and
`bash /app/scripts/verifier-rebuild.sh` to rebuild the binary after editing
any package under `internal/`.
