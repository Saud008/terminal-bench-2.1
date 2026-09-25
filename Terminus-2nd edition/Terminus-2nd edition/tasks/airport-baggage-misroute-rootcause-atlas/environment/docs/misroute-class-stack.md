# misroute-class-stack.md

When multiple failure signals apply to one scan row, classify using this stack (lowest level wins for histogram primary cause):

| Level | Cause code |
|-------|------------|
| 0 | OUTAGE_SUPPRESSED |
| 1 | CONNECTION_INFEASIBLE |
| 2 | BELT_UNMAPPED |
| 3 | ROUTED_OK |

Atlas misroute_count includes levels 1 and 2 only. Level 0 increments suppressed_count. Level 3 is routed success.
