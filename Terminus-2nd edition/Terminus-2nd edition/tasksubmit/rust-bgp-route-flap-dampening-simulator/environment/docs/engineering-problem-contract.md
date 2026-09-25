# Engineering problem contract — rust-bgp-route-flap-dampening-simulator

Core concept: BGP Route Flap Dampening figure-of-merit tracking per peer and prefix using RFC 2439 style suppress and reuse thresholds, plus a reuse-timer forecast publish that projects continuous exponential decay into operator planning JSONL.

Workflow: admit UPDATE streams into a scenario lock, reapply into a flap ledger with peer-specific dampening rows, emit a suppression atlas, then emit a reuse-timer forecast with closed-form ms_to_reuse, slot anchor binding, and SHA-256 slot digests.

Primary artifact: /app/output reuse-timer forecast JSONL (alongside the existing suppression atlas) whose columns and retention rules are defined in /app/docs/reuse-timer-forecast.md.

Distinct from a flat atlas copy: forecast math is continuous half-life inversion against the peer reuse ceiling, and slot_digest binds peer, prefix, penalty, reuse threshold, ms_to_reuse, and anchor together for operational fleet rollout reviews.
