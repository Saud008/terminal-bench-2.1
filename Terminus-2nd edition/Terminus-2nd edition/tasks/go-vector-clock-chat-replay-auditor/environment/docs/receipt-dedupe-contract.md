# Receipt and duplicate suppression contract

## Receipt payload

| Field | Type |
|-------|------|
| ref_event_id | string |
| recipient | string |
| delivered_clock | object | Vector clock map at delivery |

## Receipt validation

A receipt is valid when ref_event_id exists in staging and delivered_clock happens-before or equals the referenced event vector_clock after merge rules. Otherwise emit receipt_mismatch.

## Duplicate suppression key

Duplicate delivery is two receipt events with the same ref_event_id and recipient. Keep the receipt with the lexicographically smaller event_id. Suppress the other from timeline and emit duplicate_delivery for the suppressed receipt.

## Timeline visibility

Suppressed duplicate receipts do not appear in audit-timeline.jsonl rows.
