# Release ledger schema

Path: /app/work/ledger.json

```json
{
  "next_sequence": 1,
  "entries": [
    {
      "sequence": 1,
      "quarantine_id": "04Rx-0001-sp",
      "class": "spam",
      "status": "released",
      "queue_id": "AAA11101"
    }
  ]
}
```

Rules:

- next_sequence is the next sequence number to assign on a successful release only.
- Failed attempts append entries without sequence and do not advance next_sequence.
- duplicate_skipped requests do not append ledger rows.
- ledger_tail_sequence in export is the highest sequence among released entries, or zero when none.
