# Guild treasury attestation control plane

`guildbankd` hosts the host-local treasury trust-admission surface for vault stack-split authenticity, gold withdraw admission, bound transfer-out refusal, interest-journal anti-replay, and sealed audit attestation.

Security contracts live under `/app/docs/`. Trust manifest: `/app/config/guildbank.json`.
Treasury trust journal: `/app/work/guildbank.db`. Sealed attestation export: `/app/output/guild-audit.json`.

Binary: `/usr/local/bin/guildbankd` with `serve --config /app/config/guildbank.json` on port 8080.
