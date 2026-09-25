You need an offline access-decision admission tool that decides whether substation switching-order procedures may be trusted for sealed unsafe-step audit export on this host. The tool stages a tamper-evident yard topology snapshot and lockout-authorization ticket, applies LOTO authenticity, interlock deny-overrides, energization-reachability integrity, parallel-path isolation gates, and step-index authenticity over switching-step batches, and publishes a digest-sealed verify-order attestation with audit_digest only when those gates hold. There is no remote SCADA or EMS and no outbound network step.

relayctl at /app/bin/relayctl is that tool. Operators run compile-yard to admit yard scenarios and stage trust metadata, then verify-order to evaluate the switching-order batch and seal the attestation.

## Operator surface

CLI flags and defaults live in /app/docs/cli-surface.md.

relayctl compile-yard --seed SEED --scenario NAME must admit one yard scenario, stage /app/var/sub/yard.snapshot as the tamper-evident topology witness, and bind /app/var/sub/loto.ticket as the seed-scoped lockout-authorization ticket before any verify-order call is allowed to read them.

relayctl verify-order --seed SEED --scenario NAME --output PATH must evaluate the admitted switching-step batch against those staged witnesses and publish a digest-sealed attestation at the caller path under /app/output/. Default contracts refuse sealed export when authenticity gates are unset or drifted.

## Integrity policy

Field-level trust rules live in the docs below. Admission must enforce every gate before sealing:

- tamper-evident yard topology witness: /app/docs/bus-topology-schema.md
- lockout-authorization ticket authenticity: /app/docs/lockout-tag-policy.md
- energization-reachability integrity under closed breakers: /app/docs/energization-propagation-contract.md
- interlock deny-overrides on close and open: /app/docs/interlock-constraint-catalog.md
- per-step admit/deny diagnostics and reason authenticity: /app/docs/switching-step-contract.md, /app/docs/unsafe-diagnostic-emit.md
- five-layer topology/energization/lockout/interlock/step-index audit ladder: /app/docs/step-order-audit-ladder.md
- parallel-path isolation authorization: /app/docs/parallel-path-isolation-rules.md
- fixture catalog: /app/docs/scenario-catalog.md
- sealed attestation math: /app/docs/verifier-output-contract.md
- trust admission workflow: /app/docs/trust-admission-workflow.md

Authorization constraints that must hold for every successful attestation:

- Active lockout tags deny operations on tagged equipment including bus targets.
- requires_isolation denies close when the target bus is already energized without isolation clearance.
- parallel_path_guard denies open when the simulated open would split energized sections without authorization.
- Out-of-order step_index skips are flagged; reason_codes and energized_buses are sorted; audit_digest binds unsafe_count and the reason multiset.
- Yard load_seq increments on each compile-yard for the same cache so ticket binding stays tamper-evident across re-admits.

## Paths and fixtures

Primary artifacts are /app/var/sub/yard.snapshot (tamper-evident staging after admitted yard load), /app/var/sub/loto.ticket (lockout-authorization ticket bound during compile-yard), and the caller-chosen path under /app/output/ (digest-sealed verify-order attestation with audit_digest). Bundled fixtures live under /app/fixtures. Hidden verifier trees may appear under /opt/verifier-fixtures and via TB3_SCENARIO_DIR. Optional helpers under /app/scripts/ are outside the trust-admission hot path and are not authoritative for sealed export digests. Do not edit /app/docs/, /app/fixtures/, or anything under /tests/.
