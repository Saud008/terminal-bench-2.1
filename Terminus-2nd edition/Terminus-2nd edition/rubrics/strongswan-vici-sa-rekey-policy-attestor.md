# Platform rubric — strongswan-vici-sa-rekey-policy-attestor

**Task folder:** tasks/strongswan-vici-sa-rekey-policy-attestor/
**Written:** 2026-07-19T15:55:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent enforces CHILD_SA delete-before-rekey ordering before accepting rekey events, +3
Agent rejects traffic-selector narrowing on rekey and keeps widen policy faithful, +3
Agent tracks IKE unique-id slot lifecycle without uid reuse across rekey, +3
Agent keeps event log_seq monotonic across rekey and stages /app/state/rekey-snapshot.json, +3
Agent exports /app/output/rekey-report.json from the staged manifest only with matching active_spi_out, +3
Agent honors VERIFIER_INITIATOR_OFFSET and hidden /opt/verifier-fixtures traces, +2
Agent rebuilds vicireplay with go build after editing fsm/childsa/ikesa/sequence/export/replay packages, +2
Agent leaves /app/docs, /app/fixtures, and /app/config unchanged, +1
Agent only patches the rekey gate while selector widen and uid map stay wrong, -3
Agent hardcodes rekey-report.json without reading the staged snapshot manifest, -3
Agent edits tests or /opt/verifier-fixtures to weaken hidden overlap or order traps, -5
