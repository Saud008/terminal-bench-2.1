# Changetype audit contract

apply writes rows into an SQLite file. Table layout:

```sql
CREATE TABLE audit_ops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  seed TEXT NOT NULL,
  seq INTEGER NOT NULL,
  dn TEXT NOT NULL,
  changetype TEXT NOT NULL,
  detail TEXT NOT NULL
);
```

One row per applied change record, seq starting at 1 in apply order. detail is a short summary: add, modify:N (N is the operation count), or delete.

audit-query --export writes:

```json
{"seed": "<seed>", "operations": [{"seq": 1, "dn": "...", "changetype": "...", "detail": "..."}]}
```

operations is ordered by seq ascending.
