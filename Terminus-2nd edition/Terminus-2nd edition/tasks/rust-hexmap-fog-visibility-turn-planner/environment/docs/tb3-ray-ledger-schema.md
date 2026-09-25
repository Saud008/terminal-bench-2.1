# LOS ray ledger schema

Path: `/app/work/los-rays/<run-id>.jsonl`

One JSON object per line for every unit×cell pair:

```json
{"run_id":"r1","unit_id":"u1","q":1,"r":0,"in_radius":true,"clear_los":true}
```

`in_radius` is true when cube distance ≤ the unit's vision radius. `clear_los` follows the raycast and elevation rules.
