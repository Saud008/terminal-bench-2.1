# Workspace atlas schema

wgpatlas-workspace.json includes run_id, site, peers, overlaps, route_conflicts, workspace_fingerprint.

Ingest stage materializes /app/work/{run-id}-ingest.json before analyze consumes it. Example: /app/work/run-ing-ingest.json after ingest --run-id run-ing.

workspace_fingerprint hashes run_id, each peer public_key and allowed_ips and disabled flag, overlaps array, and disabled_skipped list from policy.
