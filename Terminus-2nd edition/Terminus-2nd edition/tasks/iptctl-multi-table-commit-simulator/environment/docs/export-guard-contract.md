# Export guard contract

`export_gate.sh` runs immediately before export. Failure aborts export with exit code **4** and must not write the report file. Its job is limited to validating internal binding consistency of the frozen staging snapshot and its sibling merge-staging artifact before report generation starts.

## Checks

1. **Plan binding** — load the snapshot, read `restore_path` and frozen `phase_config`, and recompute `compute_plan_digest(restore_path, staging.phase_config)` (same helper as `/app/tools/simulate.py`). Compare the result to `staging.binding.plan_digest`. Do **not** call `lib_plan_digest` / `plan_binding.sh`, hardcode specific `phase_config` values, or consult live phase module output during export.
2. **Merge-staging presence** — sibling merge-staging file must exist for the snapshot path (see `staging-schema.md` for the filename rule).
3. **Merge-staging digest** — sibling `merge_staging_digest` must match `staging.binding.merge_staging_digest` and the canonical payload defined in `/app/docs/iptctl-commit-pipeline.md`.

`verify_staging_binding` must be independently invocable. It should accept any staging snapshot whose binding fields and merge-staging sibling are internally coherent, even if another export-stage library is temporarily swapped and the eventual report content would be wrong. Report correctness is enforced separately by export-path tests; the guard must not depend on `report_emit.sh` behavior.

The guard reads only:

- the staging JSON bytes on disk,
- the restore file at `staging.restore_path` (for digest recomputation),
- the merge-staging sibling path derived from the snapshot filename,

and the frozen `phase_config` object embedded in the snapshot. It must not call `lib_plan_digest`, re-run phase modules, read `IPT_CFG_*` environment variables, or assert specific `phase_config` token values beyond what `compute_plan_digest` already hashes.

## Independent invocation

`export_gate.sh` exposes `verify_staging_binding` for direct use:

```bash
source /app/lib/export_gate.sh
verify_staging_binding /app/state/example.staging.json
echo $?
```

Exit **0** means internal binding consistency only. Exit **4** means missing sibling, merge digest mismatch, or plan binding mismatch. The function does not run simulation, write report JSON, or source `report_emit.sh`. A coherent snapshot may pass while `report_emit.sh` is broken and would emit wrong `nat_active` or `conntrack_order` fields.

## Exit codes

| Code | Condition |
|------|-----------|
| 0 | Guard passed |
| 4 | Missing sibling, digest mismatch, or plan binding mismatch |

Export must consume snapshot tables and frozen `phase_config` only. Re-parsing the restore file for simulation or reading live phase module output during export violates this contract even when outputs appear correct for bundled fixtures.
