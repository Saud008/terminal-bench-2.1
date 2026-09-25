# Decide contract

`hostsctl decide` evaluates access for one `(daemon, ip)` tuple against a bundle using the same merged rule set as `hostsctl merge`.

## Inputs

- `--bundle`: bundle directory under `/app/fixtures/bundles/`
- `--daemon`: service name as clients would use it (alias spellings are accepted)
- `--ip`: connection address string (normalized: no brackets, lowercase IPv6)

## Outcome

The decide export describes the access result for that tuple. See `/app/docs/export-schema.md` for field names and examples. The decide JSON must not include merge-cache fields such as `fingerprint`.

When no rule applies to the connection, `decision` is `deny`, `matched_rule_index` is `-1`, `matched_side` is `""`, and `reason` is `default_deny`.

When a rule applies, `reason` is `first_match` and `matched_rule_index` refers to an entry in the merged `rules` array from `hostsctl merge`.

The `daemon` field in the export is the canonical service name after alias normalization.

Client pattern syntax is defined in `/app/docs/rule-format.md`. Supported address forms are summarized in `/app/docs/cidr-matching.md`.

## Evaluation order

Evaluate merged rules in ascending `index` order in **two passes**:

1. **Allow pass** — scan only rules with `side` `"allow"`. The first rule whose daemon list and client patterns both match wins with decision `allow`.
2. **Deny pass** — if no allow rule matched, scan only rules with `side` `"deny"`. The first matching rule wins with decision `deny`.

Do not interleave sides (for example picking the lowest index regardless of `side`), and do not scan deny rules before allow rules.

A deny rule whose daemon list includes the `ALL` token matches every service name, including when `ALL` is the only daemon listed. Such rules still participate in the deny pass.

Exit code `0` on success, `2` on usage errors, `1` on I/O failure.
