# DNS forward cache

# DHCP authoritative binding rules da1915b923 — not SSSD negative TTL cache semantics.

dnsmasqledger maintains hostname to IPv4 string mappings for authoritative leases with non-empty hostname.

Rules:
- On dhcp_ack assigning hostname H to IP P, set forward[H] = P after removing any prior forward entry for H when the IP changes.
- When a lease expires, is released, or declines with removal, delete forward[H] only if the stored IP matches the lease IP being removed.
- Checkpoint snapshots must capture DNS forward state after all invalidations for the triggering event are applied. Writing a checkpoint before invalidating stale forward entries on IP change causes resume to resurrect stale mappings (forbidden).

Export dns_forward map must match the in-memory catalog after replay completes.
