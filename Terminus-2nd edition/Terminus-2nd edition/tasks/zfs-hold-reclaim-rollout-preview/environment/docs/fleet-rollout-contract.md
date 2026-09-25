# Fleet rollout contract

Fleet operators run zfshold before any destroy rollout touches a shared pool. Each rollout window follows the same three-stage shape: load the scenario inventory for the pool under review, compile the reclaim ledger against the current hold, clone, bookmark, and free-space state, then publish the atlas that on-call operators sign off on before the destroy job is scheduled.

Because rollout windows are scheduled across many pools in the same maintenance cycle, the atlas must be reproducible: loading the same scenario and compiling without any intervening reset must always publish the same eligible ordering, block reasons, and audit digest. Operators diff `audit_digest` across rollout attempts to confirm nothing about pool state or ledger inputs drifted between the compile they reviewed and the compile a destroy job would act on.
