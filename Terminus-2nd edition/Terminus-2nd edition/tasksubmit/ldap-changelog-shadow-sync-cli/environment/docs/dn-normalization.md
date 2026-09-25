# DN normalization

Before staging or database writes, compute `normalized_dn`:

1. Trim surrounding whitespace from the raw `dn` value.
2. Split into RDN components on unescaped commas (`,` not preceded by `\`).
3. For each component, split on the first unescaped `=` into attribute type and value.
4. Lowercase **only** the attribute type; preserve the value string exactly (including interior spaces and case).
5. Rejoin components with `,` (no extra spaces).

Examples:

| Raw DN | normalized_dn |
|--------|---------------|
| `CN=Alice,OU=People,dc=Example,dc=com` | `cn=Alice,ou=People,dc=Example,dc=com` |
| `cn=Bob Smith,ou=Staff,dc=test,dc=local` | `cn=Bob Smith,ou=Staff,dc=test,dc=local` |

Two changelog records whose raw `dn` differs only by attribute-type case refer to the same shadow entry.
