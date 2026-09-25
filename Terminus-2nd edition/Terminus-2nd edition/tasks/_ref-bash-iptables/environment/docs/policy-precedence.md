# Chain policy precedence

iptables filter chains map to nft inet filter base chains:

| iptables | nft chain | hook | default hook priority |
|----------|-----------|------|----------------------|
| INPUT | input | input | 0 |
| FORWARD | forward | forward | 0 |
| OUTPUT | output | output | 0 |

`policy_precedence` rows in staging-meta are sorted by `hook_priority` ascending, then chain name ascending.

Each row contains:

- `chain` — uppercase iptables name
- `nft_chain` — lowercase nft name
- `iptables_policy` — ACCEPT or DROP from the `:CHAIN POLICY` declaration
- `nft_policy` — accept or drop from the nft `policy` keyword
- `hook_priority` — integer from table above unless the nft excerpt declares `priority N` explicitly
- `precedence_rank` — dense rank starting at 1 after sorting by hook_priority

Export emits a **high** finding when `iptables_policy` normalized equals the nft policy normalized but `hook_priority` ordering relative to other chains disagrees with the nft excerpt declaration order for forward vs input when policies differ.

For matching policies on mapped chains, precedence_rank in staging must mirror nft chain declaration order in the source file (first declared chain gets lower rank).

Bracket counters on iptables chain declarations (`:INPUT ACCEPT [pkts:bytes]`) must be copied into the policy row `counter_packets` and `counter_bytes` fields on the iptables policy tuple (ordinal 0).
