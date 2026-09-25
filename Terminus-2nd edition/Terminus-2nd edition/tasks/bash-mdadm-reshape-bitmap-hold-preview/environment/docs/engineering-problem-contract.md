# Engineering problem contract

Linux software-RAID reshape is a geometry mutation: stripe width, parity layout, and spare inclusion change while the array stays online. The failure envelope is not a generic hold checklist. It is the interaction of write-intent bitmap arming, spare-slot reservation, degraded active-disk floors, illegal level hops, and maintenance hour budgets.

Root causes that matter here are bitmap-armed freezes, second-spare holds that the first-spare check misses, raid5 floors set too low, raid6→raid5 hops accepted by a loose transition table, and hour comparisons that treat equal budgets as over-budget. Observable symptoms are eligible-set drift, block-reason drift, unstable salted names across load_seq, and digest strings that do not match the ledger.

The verifier demands RAID-native reasoning: age is not a snapshot TXG; criticality ranks reshape urgency; digest sealing binds eligible names to block reasons after policies run. Do not treat this as a reconnect cutover or ZFS reclaim twin. Salted names use hashlib-style SHA-256 truncation as defined in array-fleet-schema.md.

