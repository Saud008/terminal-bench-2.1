# partyd

Host-local occupancy-attestation control plane with a SQLite-backed lifecycle and digest-sealed
audit publication.

See `/app/docs/` for attestation contracts. Operator binary: `/usr/local/bin/partyd`.

## Layout

| Path | Role |
|------|------|
| `/app/cmd/partyd` | CLI entrypoint |
| `/app/internal/party/` | Lifecycle admission and staging surfaces |
| `/app/internal/audit/` | Canonical digest + chained ledger |
| `/app/internal/cleanup/` | Invite TTL sweeper |
| `/app/internal/store/` | SQLite schema and helpers |
| `/app/config/party.json` | Default limits and paths |
| `/app/state/` | Durable occupancy checkpoint ledger |
| `/app/output/` | Published occupancy audit |
