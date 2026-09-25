Occupancy-audit security operators run the host-local partyd occupancy-attestation control plane at /usr/local/bin/partyd. Each offline pass admits party lifecycle mutations into a tamper-evident chained staging ledger, evaluates invite-acceptance authenticity, member-cap admission, sweep-epoch retirement gates, and occupancy reconciliation, then publishes a digest-sealed party audit only when the verified checkpoint chain matches the attestation contracts - without a remote party cluster or outbound network step. This is a security occupancy-attestation and sealed-audit workflow: keep digest chaining, acceptance authenticity, cap admission, sweep retirement, and digest-bound audit attestation aligned. It is not a generic Go HTTP party engine, daemon rebuild, pytest harness, or CI tooling exercise.

Security contracts under /app/docs/:

- chained occupancy staging ledger: /app/docs/audit-snapshot.md
- canonical digest encoding: /app/docs/staging-digest.md
- digest-sealed audit export: /app/docs/export-schema.md
- sweep-epoch retirement gates: /app/docs/sweep-contract.md
- party lifecycle admission surface: /app/docs/party-contract.md
- invite acceptance authenticity: /app/docs/invite-lifecycle.md
- idempotent accept anti-replay: /app/docs/idempotency.md
- member-cap admission: /app/docs/member-cap.md

Primary artifacts:

  /app/state/party-audit-snapshot.json - append-only chained occupancy checkpoints
  /app/output/party-audit.json - sealed report bound to the verified staged entry

partyd serve --config /app/config/party.json must host the occupancy attestation surface on port 8080. Party creation, invitations, idempotent acceptance, leader disconnect, and TTL sweeps must append checkpoints, advance sweep epochs, and refuse publication when chain verification fails. Publish must seal /app/output/party-audit.json only from the verified staged entry for the requested party. Ledger chain, sequence counters, and sweep epoch are durable across daemon restarts. Header X-Test-Mono-Ms pins the monotonic clock for deterministic attestation windows.

LegacyCapGuard in /app/internal/party/capwrap.go and LegacySealDigest in /app/internal/audit/legacy_seal.go support an archived format and are not on the staging or report-publication path. Staging query helpers under /app/internal/store/ predate the v2 ledger contract.

Bundled fixtures live under /app/fixtures. Hidden verifier seeds may appear under /opt/verifier-fixtures. Do not edit /app/docs/, /app/config/, /app/fixtures/, /tests/, /app/cmd/partyd/main.go, /app/internal/api/server.go, /app/internal/party/handler.go, or /app/internal/party/dao.go. Do not run apt-get, pip install, or other network installs.
