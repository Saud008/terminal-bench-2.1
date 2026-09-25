# Sentinel database schema

Path: /app/work/freshness-scans.db

Table scans(id, seed, pack, summary_json, active).

Inserting a scan for a seed must deactivate prior active rows for that seed regardless of pack.

LatestScan returns the active row for the requested seed and pack.
