# Scope precedence

Scope values are entry, one, or subtree. Entry matches only the target DN. One matches the target DN or direct children one level deeper. Subtree matches the target DN or any descendant at any depth.

Subtree scope includes the target entry itself. An ACE on ou=people with subtree scope applies to cn=alice under that organizational unit and to ou=people itself when the probe entry matches.

## Scope weight in ACE ranking

When two applicable ACE rows share the same target depth, scope breaks ties during trust ranking (`deny-before-allow.md`):

| Scope | Weight |
| --- | ---: |
| `entry` | 300 |
| `one` | 200 |
| `subtree` | 100 |

Higher weight wins. An `entry`-scoped ACE on a target beats a `subtree`-scoped ACE on an ancestor at the same effective depth tie.
