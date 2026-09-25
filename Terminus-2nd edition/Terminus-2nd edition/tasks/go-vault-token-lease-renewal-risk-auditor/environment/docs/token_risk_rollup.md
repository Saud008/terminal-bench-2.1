# Token risk rollup schema

Path: `/app/output/token_risk_rollup.json`

Audit time base: RFC3339 UTC timestamp from `audit_anchor.txt` in the config directory.

## tokens

One object per staged ledger row. Sorted by `token_id` ascending, then `renewal_seq` ascending.

| Field | Type | Notes |
|-------|------|-------|
| token_id | string | |
| renewal_seq | int | |
| lineage_root | string | |
| lineage_depth | int | |
| is_orphan | bool | |
| admission | string | `granted` or `denied` |
| risk_bucket | string | `critical`, `high`, `medium`, or `low` |
| risk_score | int | Integer score; upper bound 200 |
| seconds_remaining | int | Non-negative |
| expires_at | string | RFC3339 UTC with `Z` |

## lineage_edges

| Field | Type |
|-------|------|
| parent_token | string |
| child_token | string |

One object per unique non-empty `delegated_parent` / `token_id` pair from staging. Sorted by `parent_token`, then `child_token`.

## lineage_roots

One object per distinct `lineage_root` among staged rows. Sorted by `lineage_root` ascending.

| Field | Type | Notes |
|-------|------|-------|
| lineage_root | string | Group key |
| token_count | int | Distinct `token_id` values in the group |
| row_count | int | Staged rows in the group |
| max_risk_score | int | |
| worst_bucket | string | Most severe `risk_bucket` in the group (`critical` > `high` > `medium` > `low`) |
| blast_radius | int | Distinct `token_id` values with `lineage_depth` > 0 |

## totals

| Field | Type | Notes |
|-------|------|-------|
| token_count | int | Length of `tokens` |
| distinct_token_count | int | Distinct `token_id` across staged rows |
| orphan_count | int | Rows with `is_orphan` true |
| critical_count | int | Rows with `risk_bucket` `critical` |
| denied_count | int | Rows with `admission` `denied` |
| cycle_count | int | Rows whose `lineage_root` starts with `cycle:` |
