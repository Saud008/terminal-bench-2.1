# Cutover rollout operations contract

Fleet operators run hciroll before any adapter cutover window touches a shared host's Bluetooth devices. Each cutover window follows the same three-stage shape: scan the scenario inventory for the adapter roster under review, compile the reconnect ledger against the current pairing, resume-hold, power-sequence, and reconnect-storm state, then publish the rollout atlas that on-call operators sign off on before the cutover job is scheduled.

Because cutover windows are scheduled across many hosts in the same rollout cycle, the atlas must be reproducible: scanning the same scenario and compiling without any intervening state reset must always publish the same eligible rank, block reasons, and audit digest. Operators diff `audit_digest` across publish attempts to confirm nothing about device state or ledger inputs drifted between the compile they reviewed and the compile a cutover job would act on.

`cutover_window_min` in the fleet inventory is descriptive fleet metadata carried through the ledger and atlas; it does not gate eligibility on its own.
