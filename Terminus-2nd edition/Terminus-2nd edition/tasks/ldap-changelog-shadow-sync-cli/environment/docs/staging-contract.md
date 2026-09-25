# Staging contract

Path: `/app/state/changelog-staging.jsonl`

One JSON object per applied changelog record (skipped replays do not append lines). Keys:

| Field | Type | Meaning |
|-------|------|---------|
| `normalized_dn` | string | Normalized DN after ingest |
| `change_number` | int | From LDIF `changeNumber` |
| `usn_changed` | int | From LDIF `uSNChanged` |
| `changetype` | string | `add`, `delete`, or `modify` |
| `attrs` | object | Post-change attribute map for add/modify; omitted on delete |
| `modify_ops` | array | Present on modify records; preserves LDIF op order |

## Attribute-name canonicalization

LDAP attribute names are case-insensitive. Before writing shadow rows or staging:

- Lowercase every attribute **name** used as a key in `attrs`.
- Lowercase every `modify_ops[].attr` value.
- Preserve attribute **values** exactly (aside from the usual LDIF line trim of surrounding whitespace).

Example: LDIF `Mail: Alice@Example.com` stages as `"mail": "Alice@Example.com"`. LDIF `replace: Title` stages as `"attr": "title"`.

## Ordering

Staging lines append in ascending `changeNumber` order (the apply order), which may differ from physical file order when a changelog lists records out of sequence.

The shadow SQLite table must match the final attribute state implied by staging.
