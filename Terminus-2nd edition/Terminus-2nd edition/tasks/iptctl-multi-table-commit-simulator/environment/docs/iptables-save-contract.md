# iptables-restore simulation contract

## Supported restore subset

Files use `iptables-save` text format with tables `*mangle`, `*nat`, `*filter`, chain policies, append rules, and `COMMIT`.

| Line | Meaning |
|------|---------|
| `*TABLE` | Begin table block |
| `:CHAIN POLICY [pkts:bytes]` | Chain default policy and baseline counters |
| `-A CHAIN ... [pkts:bytes]` | Append rule; optional counter suffix |
| `COMMIT` | End table block |

## Table commit order

Simulation walks committed tables in an order that respects mark visibility. NAT rules that match `-m mark` observe marks recorded only from mangle rules committed earlier in the walk. If nat is committed before the mangle rule that sets a required mark, `nat_active` stays false for that matcher.

Phase ingest modules must analyze parsed tables and emit commit order accordingly. See `/app/docs/phase-config-contract.md`.

Only tables present in the file are committed. Skipped tables are omitted from `commit_order`.

## Seed shuffle (verifier)

For each table block, reorder only `-A` lines deterministically:

```text
sort_key = sha256("<seed>:<table>:<rule_id>").hexdigest()
```

`rule_id` is the 0-based index of the `-A` line within its table block **before** shuffle. Policy lines and `COMMIT` are not shuffled. This identifier is **per table** — do not use a global counter across `mangle`, `nat`, and `filter` when computing shuffle keys. Parsed staging tables and ingest validation use the field name `rule_id` (see `/app/tools/simulate.py`).

Exported `rules[].index` (see `/app/docs/export-schema.md`) is a separate global walk index across committed tables and is not used for shuffle.

## Mangle → NAT dependency

While walking rules in commit order:

1. Each `mangle` rule containing `-j MARK` and `--set-mark 0xNN` records mark `NN` (hex, lower case, no `0x` prefix normalization: use digits from file).
2. When a later `nat` rule matches `-m mark --mark 0xNN/0xff`, set `nat_active=true` only if mark `NN` was recorded from an already-committed `mangle` rule.

Mark bridge mode at ingest must reflect whether both rule kinds appear in the parsed restore.

## Chain policy counters

Parsed `:CHAIN` packet and byte counters must appear in export without zeroing when the restore carries non-zero baselines. Phase policy mode selection inspects parsed policy lines.

## Rule counters

Parsed `-A` packet and byte counters from the optional `[pkts:bytes]` suffix must survive export when the restore carries non-zero suffixes. Missing suffix exports as `0`. Phase rule counter mode selection inspects parsed append lines.

## Conntrack match order

Collect `-m conntrack` rules from `filter` and `mangle` tables during the commit walk (see `/app/docs/export-schema.md`). Eligible rules are those whose trimmed `spec` contains `-m conntrack` and do not contain **both** `-j CT` and `--notrack`. Rules with only `-j CT --notrack` and no `-m conntrack` are omitted.

### Collection order (both ct_mode values)

1. Walk committed tables in `phase_config.commit_order`.
2. Within each table, walk shuffled `-A` lines in chain declaration order (post seed shuffle).
3. Append each eligible rule from `filter` or `mangle` to `conntrack_order` in encounter order.

### ct_mode chain

When frozen `phase_config.ct_mode` is `chain`, export `conntrack_order` in collection order. Do not reorder by `--ctstate`, table name, or chain name.

### ct_mode lexical sort dimensions

When frozen `phase_config.ct_mode` is `lexical`, sort the collected list after the commit walk using exactly one key:

| Dimension | Rule |
|-----------|------|
| Sort key | The rule `spec` string (trimmed text after `-A CHAIN`, without the optional `[pkts:bytes]` suffix) |
| Comparison | Ascending byte-wise lexical order (plain string less-than) |
| Tie-breaking | Stable sort: preserve collection order when two specs are identical |

Do not sort on `table`, `chain`, `--ctstate`, or mark fields. Lexical mode affects only `conntrack_order`; it does not reorder `rules` or `policies`.

Phase module wiring is documented in `/app/docs/phase-config-contract.md` and `/app/docs/iptctl-commit-pipeline.md`. Parsed tables are snapshotted at ingest; export must not re-parse restore files.
