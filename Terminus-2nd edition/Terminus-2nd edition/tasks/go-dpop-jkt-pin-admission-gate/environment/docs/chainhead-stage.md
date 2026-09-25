# Chainhead staging

After every `/gate/session/open`-established session receives a
`/gate/proof/check` decision (admit **or** deny), the gate stages
`/app/state/chainhead.json`:

```json
{
  "version": 1,
  "principal": "...",
  "session": "...",
  "jkt": "...",
  "chain_seq": 1,
  "chain_head": "<hex>",
  "admitted_total": 0,
  "denied_total": 0,
  "deny_totals": {
    "ticket_invalid": 0,
    "alg_rejected": 0,
    "bad_signature": 0,
    "jkt_mismatch": 0,
    "htm_mismatch": 0,
    "htu_mismatch": 0,
    "iat_skew": 0,
    "jti_replay": 0
  },
  "chain_events": [
    {"seq": 1, "jti": "...", "verdict": "admit"}
  ]
}
```

## Head formula

```
chain_head = hex(sha256(prev_head || ":" || principal || ":" || session || ":" || decimal_chain_seq || ":" || verdict_token))
```

`prev_head` is the empty string for the first staged snapshot in a process's
write chain; thereafter it is the previous snapshot's `chain_head` for the
same `(principal, session)`. `verdict_token` is `"admit:" + jti` for an
admitted decision or `"deny:" + reason` for a denied one. `chain_seq`
increments by one on every staged decision, admit or deny.

## chain_events ordering

`chain_events` holds every decision staged so far for this
`(principal, session)`, **in ascending `seq` order** (the order the
decisions actually happened in). It must never be reordered by any other
key — in particular, sorting by `jti` scrambles the sequence and breaks any
consumer that reads `chain_events[-1]` to find the latest decision.
