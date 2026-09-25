Identity-security operators need a host-local Linux-PAM authentication-path authorization control plane at `/app/bin/pamtrace`. The plane admits offline PAM configuration bundles, expands include and substack trust boundaries into a sealed stack ledger, evaluates required / requisite / sufficient / optional control-flag gates plus nested group-membership policy, and publishes a digest-bound auth-path attestation for a named service and subject. There is no live PAM host and no outbound network step. This is a security authorization attestation workflow; keep scenario admission integrity, include/substack expansion, control-flag trust gates, module-outcome lookup, group-closure authz, ledger fingerprints, and sealed `trace_digest` export aligned. It is not a debugging, stack-repair, or generic CLI-engineering exercise.

Policy contracts under `/app/docs/`: `pam-service-grammar.md` for service-file grammar and control-flag tokens, `include-substack-contract.md` for `@include` / `@include-substack` expansion and path resolution, `control-flow-contract.md` for auth-stack control-flag evaluation, `module-outcome-contract.md` for per-subject module outcomes, `group-policy-contract.md` for nested group closure on account and auth gates, `ledger-stack-schema.md` for `/app/state/pamtrace-ledger.json`, `auth-path-trace-contract.md` for emitted attestation fields and digests, and `scenario-layout.md` for bundled scenario roots and optional `PAMTRACE_SCENARIO_OVERRIDE`.

`pamtrace` must accept offline bundles from `/app/fixtures/scenarios/` (and alternate roots when `PAMTRACE_SCENARIO_OVERRIDE` is set) and expose:

```text
pamtrace load --scenario <name> --run-id <id>
pamtrace compile --run-id <id>
pamtrace emit --run-id <id> --service <service> --subject <user> --output <path>
```

`load` must admit a scenario into run-scoped work metadata. `compile` must materialize `/app/state/pamtrace-ledger.json` with expanded per-service module sequences, outcomes, subjects, `ledger_fingerprint`, and per-service `service_fingerprint` values per `ledger-stack-schema.md`. `emit` must read that ledger only (not re-parse raw service files), apply control-flag and group-policy gates for the requested service and subject, and write attestation JSON whose `run_id`, `service`, `subject`, `subject_groups`, ordered `steps` (`index`, `module`, `control`, `result_code`, `result`), `verdict_code`, `verdict`, `reason`, and `trace_digest` match `auth-path-trace-contract.md`. The decoy `rhel6_bridge` module must stay off the load and emit hot path.

After policy-module edits under `/app/internal/`, leave `/app/bin/pamtrace` current (the verifier may invoke `/app/scripts/rebuild-pamtrace.sh`) without apt-get, pip install, or other network installs. Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`.
