# Allowed-IP overlap

Two active peers overlap when any AllowedIPs CIDR from one peer overlaps any CIDR from another using standard IP network math. Overlap edges sort by peer_a, peer_b, cidr_a, cidr_b ascending. Disabled peers do not participate in overlap detection.
