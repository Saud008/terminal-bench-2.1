Workshop-ops administrators run the host-local workshop-plan mount-plan control plane at /app/bin/workshop-plan. Each offline ops pass admits a WorkshopCollection VDF epoch, stages a digest-bound parsed snapshot, enforces required-edge and numeric semver admission barriers, computes dependency-first mount order under cycle-path gates, then publishes a sealed plan JSON only when the staging digest gate still matches. There is no live SteamCMD host or outbound workshop API. This is a system-administration host-local workshop mount-plan ops control plane; keep VDF admission, staging digest seals, semver barriers, mount-order gates, run-sequence seals, and sealed plan export aligned. It is not a generic SteamCMD CLI rebuild, bash pipeline engineering, pytest harness, or service repair exercise.

Ops contracts under /app/docs/ define the enforceable invariants:

- /app/docs/plan-contract.md — required-edge admission, numeric semver barriers, mount_order, and cycle paths
- /app/docs/staging-schema.md — digest-bound parsed-manifest.tsv and staging-meta.json layout
- /app/docs/pipeline-overview.md — admit → stage → resolve → sealed export ops stages
- /app/docs/plan-output-schema.md — sealed plan JSON fields and footer.run_seq
- /app/docs/vdf-manifest-format.md — offline WorkshopCollection manifest layout

workshop-plan plan --manifest-dir PATH --config PATH --output PATH must admit each offline WorkshopCollection epoch into digest-bound staging at /app/state/parsed-manifest.tsv and /app/state/staging-meta.json, resolve required-edge admissions and numeric semver barriers from that staged snapshot only, compute dependency-first mount_order with contract cycle paths when graphs contain cycles, and publish sealed plan JSON at the caller-provided --output path only when the staging digest gate still matches.

Successful exit 0 must persist input_fingerprint and run_seq under /app/state/run-seq.json and mirror run_seq in the plan footer. Identical manifest bytes and config must reproduce identical plan JSON and keep run_seq unchanged. A changed input fingerprint must advance run_seq. Export must refuse when the staging digest is stale or missing.

Failed-run sequence seals (exit 1 or 2): do not create, update, or increment /app/state/run-seq.json. When no prior run-seq.json exists, the sealed plan footer.run_seq must still be 1. When prior run-seq.json exists, footer.run_seq must retain that existing seq value unchanged (no fingerprint compare, no increment).

Exit guarantees: 0 when the epoch resolves cleanly; 1 when required dependencies are missing or semver constraints fail, with contract error strings recorded in the plan; 2 when a dependency cycle is present and emit_on_cycle is false, with empty mount_order and contract cycle paths in the plan.

/app/decoy/legacy_mount.sh and /app/wrap/decoy_topo.sh are retired helpers and must not influence ingest, resolve, or export. Bundled fixtures live under /app/fixtures. Hidden verifier fixtures may supply alternate epochs under /opt/verifier-fixtures. Do not edit /app/docs/, /app/fixtures/, /app/config/plan.json, or files under /tests/.
