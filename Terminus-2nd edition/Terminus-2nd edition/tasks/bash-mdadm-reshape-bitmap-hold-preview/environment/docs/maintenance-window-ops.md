# Fleet rollout contract

Fleet operators run mdreshape before any grow/reshape maintenance window touches a shared host's arrays. Each maintenance window follows the same three-stage shape: scan the scenario inventory for the host fleet under review, compile the reshape ledger against the current bitmap, spare-hold, degraded-floor, level-path, and window-hour state, then publish the atlas that on-call operators sign off on before the reshape job is scheduled.

Because maintenance windows are scheduled across many hosts in the same cycle, the atlas must be reproducible: scanning the same scenario and compiling without any intervening reset must always publish the same eligible rank, block reasons, and audit digest. Operators diff `audit_digest` across publish attempts to confirm nothing about array state or ledger inputs drifted between the compile they reviewed and the compile a reshape job would act on.
