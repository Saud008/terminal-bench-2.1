# ldif-apply CLI

Binary is built from /app/crates/ldif-apply. Run from /app after cargo build --locked --release --bin ldif-apply.

## apply

```
ldif-apply apply --input <ldif> --seed <seed> --export <json> --audit-db <sqlite>
```

Reads one LDIF file, updates the in-memory directory, writes the export JSON, and inserts audit rows for the seed. Exit 0 on success, 1 on I/O or parse failure.

## audit-query

```
ldif-apply audit-query --audit-db <sqlite> --seed <seed> --export <json>
```

Writes a JSON audit summary for the seed. Exit 0 when rows exist, 2 when the seed has no rows.
