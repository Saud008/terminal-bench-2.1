# Platform rubric — hci-bond-trust-reconnect-rollout-preview

**Task folder:** tasks/hci-bond-trust-reconnect-rollout-preview/
**Written:** 2026-07-16T16:13:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements hciroll scan/compile/publish on the Bash HCI fleet rollout baseline, +3
Agent materializes salted_id from host_salt, adapter_id, and mac during scan into inventory state, +3
Agent advances load_seq by one when rescan registers an existing run and echoes it in run-meta, +2
Agent marks trusted devices with addr_type drift and no pairing_confirmed as ineligible_pairing_required, +3
Agent treats resume_cleared as clearing a non-empty resume_token instead of blocking forever, +3
Agent blocks off_first adapters that lack disconnect-before-power recording with ineligible_power_sequence, +3
Agent counts reconnect attempts with debounce_ms collapsing rapid battery probes before storm budget, +3
Agent folds GATT UUID inventory to a lowercase unique service count in the reconnect ledger, +2
Agent ranks eligible devices by criticality ascending then mac ascending across adapters, +3
Agent publishes audit_digest as sha256 of sorted adapter|mac|eligible|reason|rank lines, +3
Agent leaves decoy stale_mac_formatter off the scan compile publish hot path, +1
Agent only patches pairing_drift while resume_cleared remains ignored, -3
Agent counts every battery probe without applying debounce_ms, -3
Agent sorts eligible rows by mac only ignoring criticality, -3
Agent hashes digest lines in ledger iteration order without sorting, -3
Agent recomputes eligibility inside publish instead of reading reconnect-ledger.json, -2
