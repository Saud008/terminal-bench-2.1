HashiCorp Nomad operators need a placement affinity atlas that correlates running allocations with CSI volume mounts, node-class hard constraints, soft affinity weights, topology spread penalties, and drain eligibility before publishing cluster reports.

nomrep is a Go CLI under /app that loads scenario bundles into a placement buffer, compiles an atlas index journal, and publishes JSON affinity atlases. Solver-visible rules live only in the cited /app/docs/ files. The decoy spreadhint module is not on the load, compile, or publish path.

Install nomrep at /usr/local/bin/nomrep with:

  nomrep load --seed <seed> --scenario <name>
  nomrep compile --seed <seed> --scenario <name>
  nomrep publish --seed <seed> --scenario <name> --output <path>

nomrep load writes /app/var/placement-buffer.json per /app/docs/placement-buffer-schema.md. CSI mount correlation uses /app/docs/csi-mountlink-contract.md. Node class hard filters and soft affinity ordering use /app/docs/node-class-precedence.md.

nomrep compile stores the active atlas row for a seed in /app/var/atlas-index.db. Persistence checks may read atlas_runs and atlas_summary through sqlite3. See /app/docs/atlas-index-schema.md.

Topology spread penalties and drain eligibility gates are in /app/docs/spread-topology.md and /app/docs/drain-eligibility.md. Reschedule totals and stale allocation suppression are in /app/docs/reschedule-stale-policy.md.

nomrep publish merges the buffer with the compiled atlas row and writes JSON to a caller path under /app/output/. Scoped allocation ids, field ordering, and audit_digest rules are in /app/docs/publish-atlas-fields.md.

Bundled scenarios are under /app/fixtures/. Coverage notes are in /app/docs/scenario-catalog.md. Overlays under /opt/verifier-fixtures/scenarios/ follow the same contracts. Snorkel verifier pytest helpers placement_atlas_math and nomrep_atlas_cli are outside the agent contract.

Compile nomrep from /app sources. Do not modify /app/docs/, /app/config/, or /app/fixtures/.
