# Lease contract

Identity: each binding is keyed by the tuple (mac, duid, iaid) rendered as mac|duid|iaid lowercase. Two clients sharing a MAC but differing DUID or IAID are distinct leases.

Tentative state: dhcp_discover and dhcp_offer populate tentative entries until dhcp_ack promotes them to authoritative leases. dhcp_decline must remove both the authoritative lease (if any) and any matching tentative entry for the identity tuple.

Authoritative flag: dhcp_ack sets authoritative true. Retransmitted ACK for an existing binding must leave authoritative true (never toggle false on replay).

Renewal: dhcp_renew extends expires_sec by adding lease_sec to the prior expires_sec anchor, not to the receipt time (now_sec). Renewal applies only to authoritative leases.

Expiry: tick advances now_sec; leases with now_sec >= expires_sec are removed and their DNS forward entries invalidated.

Release: dhcp_release removes the lease and tentative state and invalidates DNS forward for the hostname/IP pair.

Active export rows include only authoritative leases with expires_sec > now_sec.

Export field tentative_count is the number of pending tentative entries remaining in the catalog after replay completes (before export is written).
