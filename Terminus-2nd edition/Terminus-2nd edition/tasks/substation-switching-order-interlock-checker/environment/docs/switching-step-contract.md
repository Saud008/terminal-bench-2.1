# Switching step contract

Each procedure step contains:

- step_index: 1-based contiguous index
- action: open or close
- breaker_id: target breaker
- requires_isolation: optional bool; when true, close is blocked if target bus already energized via alternate path
- parallel_path_guard: optional bool; when true, open blocked if breaker isolates energized section

verify-order simulates steps in step_index order starting from initial breaker states in yard.snapshot. State is cumulative: step N+1 begins from post-step-N breaker states and energization.
