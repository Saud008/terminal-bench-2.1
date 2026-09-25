# Legal holds

Holds JSON:

```json
{
  "exact": ["audit-2024-q2"],
  "prefix": ["legal-"]
}
```

| Field | Meaning |
|-------|---------|
| exact | Archive names never pruned |
| prefix | Archive names **starting with** the prefix string are never pruned |

Legal holds apply after duplicate resolution. Held archives are always in kept_archives regardless of bucket assignment.
