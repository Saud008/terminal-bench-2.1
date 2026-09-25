# Guild treasury control plane

`guildbankd` hosts the host-local treasury admission surface for vault stack-split authenticity, gold withdraw admission, bound transfer-out refusal, interest-journal anti-replay, and audit export.

Security contracts live under `/app/docs/`. Trust manifest: `/app/config/guildbank.json`.
Treasury journal: `/app/work/guildbank.db`. Audit export: `/app/output/guild-audit.json`.

Binary: `/usr/local/bin/guildbankd` with `serve --config /app/config/guildbank.json` on port 8080.

The shipping sources under `/app` do not yet satisfy the contracts; repair and rebuild before relying on the binary.
