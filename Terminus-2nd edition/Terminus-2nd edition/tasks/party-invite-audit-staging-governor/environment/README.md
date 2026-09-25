# partyd

Host-local occupancy-attestation control plane with a SQLite-backed lifecycle and digest-sealed
audit publication.

See `/app/docs/` for operations contracts. Operator CLI: `/app/bin/partyd`.

## Layout

| Path | Role |
|------|------|
| `/app/scripts/partyd` | Bash CLI wrapper |
| `/app/lib/party/lifecycle.py` | Lifecycle admission and staging hooks |
| `/app/lib/party/{canon,ledger,stage}.py` | Canonical digest, ledger, and checkpoint staging |
| `/app/lib/party/{publish,sweeper,query}.py` | Export, sweep, and SQLite projections |
| `/app/config/party.json` | Default limits and paths |
| `/app/state/` | Durable occupancy checkpoint ledger |
| `/app/output/` | Published occupancy audit |

Archived helpers (`LegacyCapGuard`, `LegacySealDigest`) are not on the staging or report-publication path; see `/app/docs/staging-digest.md`.
