# Export isolation

On this system-administration pagestore control plane, export must read committed tables via /app/state/committed.json.

Staging data in /app/state/staging.json must not appear in export output until commit completes.

Only committed table state may be scanned when building export JSON rows.
