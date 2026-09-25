# Platform rubric — dnsmasq-lease-authoritative-renewal-skew-ledger-repair

**Task folder:** tasks/dnsmasq-lease-authoritative-renewal-skew-ledger-repair/
**Written:** 2026-07-02T10:30:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent anchors renewal expiry from prior lease end not receipt time, +3
Agent treats distinct IAID on same MAC as separate authoritative bindings, +3
Agent sets authoritative true on dhcp_ack and clears tentative rows, +3
Agent purges stale DNS forward entries when client IP changes, +3
Agent writes lease-snapshot.json with dns_forward matching export, +2
Agent persists SQLite lease rows mirroring active authoritative report, +2
Agent calls checkpoint persist before DNS invalidation on IP change, +2
Agent deletes exported PersistBeforeDNSInvalidation helper, -3
Agent renames or removes dns.Bind or dns.Invalidate package helpers, -2
Agent adds new Go source files under internal/lease package, -2
