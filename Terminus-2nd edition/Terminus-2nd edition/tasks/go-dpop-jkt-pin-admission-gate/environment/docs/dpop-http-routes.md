# DPoP HTTP routes

Binary: `/usr/local/bin/jktadmit` (mirrored at `/app/bin/jktadmit`)
Config: `/app/config/jktadmit.json`
Listen: `:8080` by default
Chainhead snapshot: `/app/state/chainhead.json`
Deny ledger: `/app/output/deny-ledger.json`
State reset helper: `/app/scripts/reset-state.sh`
Binary rebuild helper: `/app/scripts/verifier-rebuild.sh`

Proof and pin field schema: `/app/docs/jkt-thumbprint-policy.md`
Bind ticket formula: `/app/docs/vault-hmac-bind.md`
Nonce window semantics: `/app/docs/jti-nonce-window.md`
Chainhead staging schema: `/app/docs/chainhead-stage.md`
Sealed ledger schema: `/app/docs/deny-ledger-seal.md`

## Routes

| Method | Path | Role |
|--------|------|------|
| GET | `/health` | Liveness probe |
| POST | `/gate/session/open` | Verify the initial DPoP proof, pin its jkt, mint the bind ticket |
| POST | `/gate/proof/check` | Admit or deny a DPoP proof under the pinned jkt and nonce-window/skew policy |
| POST | `/gate/audit/commit` | Publish the digest-sealed deny ledger for a principal/session |

Header `X-Test-Now-Unix` pins the server's notion of "current unix second" for
the duration of that request; every skew and nonce-window computation reads
this pinned clock instead of the wall clock.

## Open body

```json
{"principal": "...", "session": "...", "dpop_proof": "<compact-dpop-proof>"}
```

The `dpop_proof` must satisfy the open-route policy in
`/app/docs/jkt-thumbprint-policy.md` (`htm` = `POST`, `htu` = the configured
`open_htu`). Missing `principal`, `session`, or `dpop_proof` is HTTP 400; a
proof that fails signature, method, URL, freshness, or pin-registry checks
is HTTP 409 with the failure reason as the response body text. On success
the response includes `bind_ticket` and `jkt` (the pinned thumbprint,
hex-encoded).

## Check body

```json
{"principal": "...", "session": "...", "bind_ticket": "...", "dpop_proof": "<compact-dpop-proof>"}
```

Missing required fields or an unbound `(principal, session)` pair is HTTP
400. A structurally valid request that is denied by policy returns HTTP 409
with a JSON body `{"verdict": "deny", "reason": "<code>"}`; an admitted
request returns HTTP 200 with `{"verdict": "admit", "reason": ""}`.

## Commit body

```json
{"principal": "...", "session": "..."}
```

Missing fields is HTTP 400. Committing before any session-open for that
principal/session is HTTP 400 (no chainhead snapshot to seal). On success
the response is `{"path": "/app/output/deny-ledger.json"}`.
