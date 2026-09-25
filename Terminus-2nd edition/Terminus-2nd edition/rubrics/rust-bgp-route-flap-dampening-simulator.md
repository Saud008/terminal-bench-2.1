# Platform rubric — rust-bgp-route-flap-dampening-simulator

**Task folder:** tasks/rust-bgp-route-flap-dampening-simulator/

Agent implements compile-scenario that writes scenario-lock.json with feed fingerprint and peer table without embedding events, +3
Agent preserves per-peer reuse_threshold from policy JSON during compile-scenario, +2
Agent sorts BGP feed events by numeric ts_ms before replay, +3
Agent applies exponential half-life penalty decay between events, +3
Agent accrues flap_penalty on withdraw after an established route, +2
Agent increments run_id in run-counter.json on each replay-feed, +2
Agent exports suppression-atlas.jsonl with stable_at_ms from ledger not last_ts_ms, +2
Agent honors TB3_HALF_LIFE_BIAS when loading peer dampening table, +2
Agent produces atlas rows matching reference math for hidden TB3 fixtures, +3
Agent patches only atlas_emit while leaving feed ordering lexicographic, -3
Agent overrides all peer reuse_threshold to a global constant in peer_table, -3
Agent applies linear decay instead of half-life exponential decay, -2
Agent accrues flap penalty on announce while suppressed instead of withdraw, -3
