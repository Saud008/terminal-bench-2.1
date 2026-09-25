# Platform rubric — substation-switching-order-interlock-checker

**Task folder:** tasks/substation-switching-order-interlock-checker/

Agent propagates bus energization through closed breakers from source buses, 3
Agent simulates switching steps cumulatively without resetting breaker state each step, 3
Agent blocks operations on equipment under active lockout tags including bus targets, 3
Agent enforces requires_isolation when target bus already energized before close, 3
Agent blocks parallel_path_guard open when simulated open splits energized sections, 3
Agent flags out_of_order when procedure step_index skips expected sequence, 2
Agent increments yard.snapshot load_seq on each compile-yard for same cache, 2
Agent writes loto.ticket during compile-yard with seed scenario load_seq binding, 2
Agent computes audit_digest with unsafe_count and reason multiset, 2
Agent sorts reason_codes and energized_buses in verify-order output rows, 2
Agent rebuilds sublock in test.sh before subprocess pytest, 2
Agent honors TB3_SCENARIO_DIR for hidden yard overlay scenarios, 2
Agent validates each switching step independently without cumulative state, -3
Agent allows close on locked breakers when lockout tags only name buses, -3
Agent ignores requires_isolation when alternate path already energizes target bus, -3
Agent permits parallel_path_guard open without simulating post-open energization, -3
Agent leaves load_seq unchanged across repeated compile-yard invocations, -2
Agent omits unsafe_count from audit_digest canonical body, -2
