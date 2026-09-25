Implement wgpatlas, a WireGuard peer policy atlas subsystem on the working Bash baseline under /app. Operators must reconcile mesh trust policy from offline WireGuard bundles under /app/sites/, materialize a normalized workspace snapshot at /app/state/wgpatlas-workspace.json, and emit a deterministic atlas JSON to a caller-provided path under /app/output/.

Install wgpatlas at /app/bin/wgpatlas with these subcommands:

  wgpatlas ingest --site <name> --run-id <id>
  wgpatlas analyze --run-id <id>
  wgpatlas export --run-id <id> --output <path>

WireGuard interface and peer stanza layout, AllowedIPs list rules, and bundled site inventory appear in /app/docs/wg-config-catalog.md. Allowed-IP overlap detection and overlap edge lexicographic sort follow /app/docs/allowed-ip-overlap-contract.md. Endpoint precedence when multiple endpoints exist for one peer follow /app/docs/endpoint-precedence-contract.md. Route table conflict detection across interfaces follows /app/docs/route-table-conflict-contract.md. Disabled peer handling from site policy follows /app/docs/disabled-peer-contract.md.

wgpatlas analyze materializes the workspace snapshot for a run id. Workspace schema, fingerprint fields, and normalized peer records appear in /app/docs/workspace-atlas-schema.md. wgpatlas export reads the workspace snapshot only and writes peer rows, overlap edges, route conflicts, and summary counters to the caller-provided output path. Emit row sort sequence, reason codes, and audit_digest rules appear in /app/docs/topology-export-contract.md.

Bundled sites live under /app/sites/ including /app/sites/coastal-mesh. Pytest helpers wgpatlas_cli_support and wgpatlas_contract_math invoke wgpatlas through subprocess and write export output to /app/output/{run-id}-atlas.json. Hidden verifier site bundles may appear under /opt/verifier-fixtures/wgpatlas/sites. Digest and CIDR helpers use hashlib and ipaddress per /app/scripts/wgpa_cidr_digest_helpers.py. Run /app/scripts/reset-state.sh before cross-run verifier cases. The mesh_rank_helper decoy module is not on the ingest or export hot path.
