# Engineering problem contract — HCI bond-trust reconnect rollout

Fleet HCI operators must decide which bonded devices are safe to reconnect during an adapter cutover window without cycling adapters against production hosts. A trustworthy preview has to reconcile pairing address-type drift, resume-token clearance, power-sequence capture, GATT service identity, and reconnect-storm budgets into one per-device eligibility outcome before a cutover job is allowed to proceed.

Root-cause gaps appear when those gates are evaluated independently instead of as a single cascaded gate chain, when publish re-derives eligibility from fixtures instead of trusting the on-disk reconnect ledger, and when eligible-device sequencing is not reproducible across repeated compiles of the same inventory.

The agent completes the hciroll scan, compile, and publish stages on the working baseline under `/app`. Sibling contracts define the fleet inventory schema, each gate's blocking condition, the criticality-then-mac eligible sequence, and the ledger and atlas JSON shapes that downstream cutover tooling depends on.
