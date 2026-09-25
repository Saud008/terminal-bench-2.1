# Platform rubric — cel-go-policy-trace-evaluator

**Task folder:** tasks/cel-go-policy-trace-evaluator/

Agent implements boolean short-circuit for AND and OR without evaluating pruned operands, +3
Agent fixes nested cel.bind so outer frames survive inner bind completion, +3
Agent canonicalizes duration operands to nanoseconds before comparison, +2
Agent applies last-wins merge for map comprehension key collisions, +2
Agent exports trace JSON listing only evaluated branches with correct has_call_count, +3
Agent rebuilds celctl after editing internal eval packages, +2
Agent wires ingest to write staging snapshot before eval or trace export, +2
Agent reads staging snapshot in eval rather than re-parsing ingest input, +2
Agent ignores decoy wrap helper for authoritative trace export, +1
Agent hardcodes trace or result JSON without running celctl eval, -3
Agent patches only ingest while leaving eval short-circuit broken, -2
Agent compares duration strings directly to raw integer nanoseconds, -2
Agent keeps first map key on collision instead of last value, -2
Agent includes pruned RHS branches in trace output, -3
