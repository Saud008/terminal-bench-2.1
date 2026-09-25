# Platform rubric — dnsmasq-lease-authoritative-renewal-skew-ledger

**Task folder:** tasks/dnsmasq-lease-authoritative-renewal-skew-ledger/

Agent implements mac|duid|iaid identity tuple keys in internal/identity/key.go, +3
Agent anchors dhcp_renew expiry extension on prior expires_sec not receipt now_sec, +3
Agent keeps dhcp_ack authoritative true on retransmitted ACK replay paths, +2
Agent clears tentative catalog rows on dhcp_decline per lease contract, +2
Agent invalidates stale DNS forward entries on IP-change ACK before checkpoint persist, +3
Agent writes lease-snapshot.json staging file matching export dns_forward during replay, +2
Agent persists authoritative SQLite lease rows mirroring active_leases export, +2
Agent handles DUID collision fixture with distinct iaid bindings on shared MAC, +3
Agent passes hidden verifier fixture logs under /opt/verifier-fixtures/replay/, +2
Agent implements only renew skew while leaving MAC-only identity keys, -3
Agent toggles authoritative false on ACK replay retransmission, -3
Agent persists checkpoint before DNS invalidation on IP-change ACK, -3
Agent leaves tentative rows after decline hidden fixture replay, -2
Agent hard-codes golden lease-report.json instead of running replay CLI, -5
