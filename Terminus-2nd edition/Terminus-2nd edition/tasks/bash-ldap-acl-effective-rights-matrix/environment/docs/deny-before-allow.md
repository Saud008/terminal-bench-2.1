# Deny before allow

When multiple ACE rules match the same subject, entry, attribute, and right, export walks applicable ACE rows in **trust rank order** and stops at the first row whose rights and attributes match the probe. That winning row determines the verdict.

Explicit ACE evaluation completes before inherited default rights from objectClass defaults are considered.

## ACE trust rank

Sort applicable ACE rows by this tuple, ascending (lower tuple wins):

1. **Target depth** — deeper target DNs win (more specific ACE).
2. **Scope weight** — `entry` (300) beats `one` (200) beats `subtree` (100).
3. **Subject specificity** — `user` subjects beat `group` subjects.
4. **Effect** — `deny` beats `allow`.
5. **`ace_id`** — lexicographic tie-breaker.

Steps 3 and 4 apply only after depth and scope are equal. **User-specific ACE rows outrank group ACE rows even when the group row is DENY and the user row is ALLOW.** Only when subject type is the same does deny beat allow.

Example: a user ALLOW on `mail` write outranks a group DENY on `mail` write at the same target depth and scope.

## Applicable ACE collection

An ACE is applicable when:

- its scope matches the probe entry (`scope-precedence.md`),
- its subject matches the probe subject (direct user DN equality, or probe subject is in the ACE group per `group-closure.md` using both `group_closure` and `group_graph` from the staging snapshot).

After sorting, scan in order. Skip rows whose `rights` omit the probe right or whose `attrs` omit the probe attribute (respect `*` wildcards). The first remaining row wins: `deny` → verdict `deny` / reason `ace_deny`; `allow` → verdict `allow` / reason `ace_allow`.

If no ACE row wins, fall back to objectClass defaults (`default-inheritance.md`), then to `no_match` deny.
