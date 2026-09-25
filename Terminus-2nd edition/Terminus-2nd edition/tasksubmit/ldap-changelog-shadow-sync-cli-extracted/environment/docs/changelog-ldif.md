# Changelog LDIF format

Each change record is one LDIF block terminated by a line containing only `-`.

Required attributes per record:

| Attribute | Meaning |
|-----------|---------|
| `dn` | Entry distinguished name (any case) |
| `changetype` | `add`, `delete`, or `modify` |
| `changeNumber` | Integer ordering key within a file |
| `uSNChanged` | Update sequence number used for replay detection |

## add

Includes attribute lines (`attr: value`) before the terminating `-`. Attribute names may appear in any case; ingest must canonicalize names to lowercase for storage.

## delete

No attribute lines required.

## modify

Uses LDIF modify directives:

```
add: attr
value line
delete: attr
replace: attr
value line
```

Operation lines apply in **file order within the record**. Do not hoist `delete` operations ahead of earlier `add`/`replace` operations in the same record—an `add` followed by `delete` of the same attribute must leave the attribute absent.

Attribute names on `add:` / `delete:` / `replace:` lines may use any case; canonicalize to lowercase before applying or staging.

## Record order

Records must be applied in ascending `changeNumber` order across the file. Physical line order in the LDIF is not authoritative when `changeNumber` values are out of sequence. `uSNChanged` values must be unique per applied change in a single directory replica stream.
