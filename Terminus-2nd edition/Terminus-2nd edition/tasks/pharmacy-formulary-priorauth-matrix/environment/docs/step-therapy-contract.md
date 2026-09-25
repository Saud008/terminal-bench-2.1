# Step therapy prerequisites

For a plan_id and target_ndc, collect all step_chains rows whose plan_id and target_ndc equal the plan and the drug's raw fixture ndc (exact string match; do not normalize target_ndc when selecting chain rows). Order those rows by sequence ascending.

Build a per-plan PA map keyed by normalized NDC (ndc-normalize-contract.md). Default every roster drug to requires_pa true, then apply active plan overrides for that plan so the map holds effective requires_pa before any step_complete evaluation.

Every prerequisite_ndc in the chain must have effective requires_pa false (step satisfied) before target_ndc publishes step_complete true. Look up each prerequisite in the PA map after normalizing prerequisite_ndc; do not use the raw prerequisite string as the map key.

If no chain exists, step_complete is true.
