# Validity output contract

Normative schemas for JSON artifacts produced by `score-validity` and `commit-ledger`.

## `/app/output/validity-decisions.json`

Top-level object fields (all required):

| Field | Type | Rule |
| --- | --- | --- |
| `scenario_id` | string | Scenario id from the loaded manifest |
| `eval_pass` | integer | Current positive pass counter after this score run |
| `reference_date` | string | ISO-8601 calendar date (`YYYY-MM-DD`) used for scoring |
| `decisions` | array of objects | One row per visa, sorted ascending by `holder_id`, then `visa_id` |
| `ledger_digest` | string | Lowercase hex SHA-256 over the digest basis below |

Each `decisions[]` row fields (all required):

| Field | Type |
| --- | --- |
| `holder_id` | string |
| `passport_id` | string |
| `visa_id` | string |
| `allowed_entry` | boolean |
| `deny_reasons` | array of strings (stable reason codes; empty when allowed) |
| `cumulative_stay_days` | integer |
| `max_stay_allowed` | integer |
| `remaining_stay_days` | integer (never negative) |

`ledger_digest` basis: SHA-256 of compact JSON (`separators=(",", ":")`, no insignificant whitespace) of the `decisions` array alone, in the sorted order above, with object keys in the field order listed for each row. File encoding is UTF-8 with a trailing newline; pretty-print indentation of the outer report is allowed, but the digest bytes are computed from the compact decisions array, not from the pretty-printed file.

`eval_pass` in this file must equal the integer stored in `/app/state/eval-pass.json` after the same `score-validity` invocation.

## `/app/output/ledger-manifest.json`

Top-level object fields (all required):

| Field | Type | Rule |
| --- | --- | --- |
| `scenario_id` | string | Sealed scenario id |
| `eval_pass` | integer | Pass counter that authorized the seal |
| `ledger_rows` | array of objects | Sorted ascending by `holder_id`, then `visa_id` |
| `ledger_digest` | string | Lowercase hex SHA-256 over the digest basis below |

Each `ledger_rows[]` entry fields (all required):

| Field | Type |
| --- | --- |
| `holder_id` | string |
| `visa_id` | string |
| `remaining_stay_days` | integer |
| `pass_num` | integer (equals `eval_pass`) |

`ledger_digest` basis: SHA-256 of compact JSON of the `ledger_rows` array alone (same compact encoding rule as decisions). Re-running `commit-ledger` with the same `eval_pass` must not change `ledger_rows` or `ledger_digest`.

## `/app/state/eval-pass.json`

Required fields: `eval_pass` (integer). `score-validity` increments it by one per successful run. `commit-ledger` requires `eval_pass > 0`.

## `/app/state/manifest-snapshot.json`

Written by `import-manifest`. Must include at least `scenario_id` (string) and `passport_count` (integer) reflecting the loaded bundle.
