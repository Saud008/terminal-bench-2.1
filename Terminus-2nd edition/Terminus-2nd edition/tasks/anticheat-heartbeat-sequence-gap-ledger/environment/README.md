# livattest — anticheat liveness attestation gate

`livattest` admits session-bound heartbeat attestations under HMAC vault tickets, enforces uint32 continuity policy with span-counted breach seals, stages a witness chain, and publishes digest-sealed attest reports.

## Layout

- `/app/cmd/livattest` — CLI entrypoint
- `/app/internal/ticket` — HMAC admission tickets
- `/app/internal/vault` — trust bind and session state
- `/app/internal/policy` — continuity admission
- `/app/internal/seal` — breach and ban seals
- `/app/internal/witness` — witness snapshot staging
- `/app/internal/export` — attest report publish
- `/app/internal/clock` — monotonic pin
- `/app/docs/` — trust and policy contracts
- `/app/config/livattest.json` — runtime config

Read `/app/docs/trust-surface.md` and `/app/docs/attest-export.md` before changing admission or publish code.
