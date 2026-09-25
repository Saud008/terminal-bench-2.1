# jti nonce window

Every admitted or would-be-admitted proof consumes its `jti` for the
lifetime of the process, scoped to the pinned `jkt` (not globally, and not
per session — two different sessions that happen to pin the **same** jkt
share one nonce-window scope; two sessions with **different** jkts never
collide even if they reuse the same `jti` string).

## Required order

For each `/gate/proof/check` call that reaches the nonce-window lookup
(i.e. it has already passed ticket, alg, signature, jkt, htm, htu, and iat
checks):

1. Look up `(jkt, jti)` in the ledger.
2. If an entry exists and its expiry is still in the future relative to the
   pinned "now", this is a **replay**: deny `jti_replay` and do **not**
   refresh the entry's expiry.
3. Otherwise, record `(jkt, jti)` with `expires_at = now + jti_window_sec`
   and continue to admission.

Membership must be checked **before** the new presentation is recorded. A
ledger implementation that records first and checks second will never detect
a replay, because the just-written entry is always found with a
not-yet-expired deadline.

## Window

`jti_window_sec` comes from `/app/config/jktadmit.json`
(`jti_window_sec`, default 120). It bounds how long a consumed `jti`
continues to block a repeat presentation; it is not a sliding cleanup
schedule — entries are checked lazily against the pinned "now" on each
lookup.

## Deny reason

A replayed `jti` increments `deny_totals.jti_replay` in both the chainhead
snapshot and the sealed ledger. The sealed ledger's `jti_replay` count must
equal the chainhead snapshot's `jti_replay` count exactly — it is never
zeroed or otherwise adjusted during sealing.
