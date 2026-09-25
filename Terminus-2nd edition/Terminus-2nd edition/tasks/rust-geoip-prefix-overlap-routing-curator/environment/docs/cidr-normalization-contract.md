# CIDR normalization contract

IPv4 CIDR strings must be normalized to network addresses with host bits cleared. Example: 203.0.113.5/24 normalizes to 203.0.113.0/24. Containment tests use normalized values only.
