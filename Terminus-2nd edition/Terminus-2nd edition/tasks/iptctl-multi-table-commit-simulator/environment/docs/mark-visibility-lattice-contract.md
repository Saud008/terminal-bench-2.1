# Mark visibility lattice contract

iptables commit simulation depends on a mark visibility lattice across mangle, nat, and filter table walks. This contract governs how parsed restore content drives ingest-time phase resolution.

## Lattice rules

When parsed tables contain both mangle `-j MARK --set-mark` rules and nat `-m mark --mark` matchers, commit order must place mangle before nat so marks recorded during the walk are visible to later nat matchers.

When no mark matchers appear in nat, mark bridge mode may remain isolated without affecting export outcomes for bundled fixtures.

Phase modules read `IPT_PARSED_PATH` during ingest and must analyze parsed rule specs. Static literals that ignore parsed content violate this contract.

Export reads frozen `phase_config` from the staging snapshot only. Export must not re-run phase modules or re-parse the restore file.

See also `/app/docs/iptables-save-contract.md` and `/app/docs/phase-config-contract.md`.
