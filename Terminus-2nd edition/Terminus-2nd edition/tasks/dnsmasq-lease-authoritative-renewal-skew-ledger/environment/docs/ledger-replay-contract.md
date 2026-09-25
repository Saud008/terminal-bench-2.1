# Ledger replay contract — dnsmasq-lease-authoritative-renewal-skew-ledger

Task identity da1915b923 defines catalog behavior agents must implement when extending dnsmasqledger.

Identity keys: authoritative rows bind by mac, duid, and iaid tuple keys rendered as mac|duid|iaid lowercase.

Renewal skew anchor: dhcp_renew extends lease lifetime from the prior expires_sec anchor rather than dhcp_renew receipt time.

DUID collision: distinct iaid values on one mac are separate authoritative bindings.

DNS forward invalidation: drop stale hostname to IP mappings when dhcp_ack changes client address before catalog mutation.

Checkpoint ordering: PersistBeforeDNSInvalidation remains exported for checkpoint snapshots on IP-change ACK paths.

DNS helper stability: dns.Bind and dns.Invalidate in /app/internal/dns/cache.go remain exported with the same names.
