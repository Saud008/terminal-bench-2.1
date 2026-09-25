# Simulation export schema

`iptctl simulate` writes JSON matching this schema.

```json
{
  "report_version": 1,
  "restore": "<basename without .v4>",
  "seed": "<seed string>",
  "commit_order": ["mangle", "nat", "filter"],
  "policies": [
    {
      "table": "filter",
      "chain": "INPUT",
      "policy": "DROP",
      "packets": 123,
      "bytes": 456
    }
  ],
  "rules": [
    {
      "table": "nat",
      "chain": "PREROUTING",
      "index": 0,
      "spec": "-m mark --mark 0x20/0xff -j DNAT --to-destination 10.0.0.5",
      "packets": 7,
      "bytes": 512,
      "nat_active": true
    }
  ],
  "conntrack_order": [
    {
      "table": "filter",
      "chain": "INPUT",
      "spec": "-m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT"
    }
  ],
  "exit_code": 0
}
```

## Field rules

| Field | Rule |
|-------|------|
| `commit_order` | Tables committed in this exact order (subset allowed if file omits a table). |
| `policies` | One entry per `:CHAIN POLICY [pkts:bytes]` line, sorted by `table`, then `chain`. |
| `rules` | One entry per `-A` line after seed shuffle, in **commit order** then chain declaration order then shuffled index. |
| `rules[].index` | Global 0-based index in commit walk order across all committed tables (not the per-table `rule_id` used for seed shuffle). |
| `rules[].packets` / `bytes` | From trailing `[pkts:bytes]` on the restore line; `0` when omitted. |
| `rules[].nat_active` | For `nat` table rules with `-m mark`, `true` only when the referenced mark was set by an earlier committed `mangle` `-j MARK --set-mark` rule. |
| `conntrack_order` | Eligible `-m conntrack` rules from `filter` and `mangle` collected during the commit walk (post-shuffle). When `phase_config.ct_mode` is `chain`, preserve collection order. When `ct_mode` is `lexical`, sort by ascending lexical order of the rule `spec` string only (see `/app/docs/iptables-save-contract.md`). Omit rules whose spec contains both `-j CT` and `--notrack`. |
