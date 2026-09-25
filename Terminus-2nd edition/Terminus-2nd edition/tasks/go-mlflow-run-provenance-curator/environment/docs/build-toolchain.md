# Build toolchain

Experiment provenance closure kernels under /app/cmd and /app/internal compile into the mlprov binary. The Dockerfile and verifier rebuild step use `go build -mod=readonly` against the module at /app.

Scientific-computing numerical kernels implement stages described in /app/docs/scientific-computing-workflow.md:

- scenario hydration into the feature-run snapshot
- SQLite closure bind for the active seed row
- eval summary certificate emission with audit_digest closure

Do not treat kernel sources as a generic service repair surface. Implement missing closure math so published certificates match the reference contracts.
