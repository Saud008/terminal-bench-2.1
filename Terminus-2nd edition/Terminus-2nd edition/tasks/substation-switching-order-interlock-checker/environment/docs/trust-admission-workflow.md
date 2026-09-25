# Trust admission workflow

Objective: decide whether a switching-order procedure may be trusted for sealed unsafe-step audit export on this host.

Admission stages a tamper-evident yard topology snapshot and lockout-authorization ticket, then applies LOTO authenticity, interlock deny-overrides, energization-reachability integrity, parallel-path isolation, and step-index authenticity gates before sealing audit_digest.

Verifier: independent Python reference math executes the relayctl CLI and compares sealed attestation fields; it does not trust in-process helpers under /app/scripts/.
