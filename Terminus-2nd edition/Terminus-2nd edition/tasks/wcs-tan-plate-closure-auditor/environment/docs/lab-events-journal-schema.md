# Laboratory events journal schema

Path: `/app/state/plate-closure.db`

`hydrate-plates` opens this SQLite database and ensures table `lab_events` exists:

| Column   | Type | Notes                                      |
|----------|------|--------------------------------------------|
| scenario | TEXT | Scenario id passed to `--scenario`         |
| verb     | TEXT | Verb name, e.g. `hydrate-plates`           |

Each successful hydrate inserts one row `(scenario, verb)`. Operators and verifiers may query the latest row with:

```sql
SELECT scenario, verb FROM lab_events ORDER BY rowid DESC LIMIT 1
```
