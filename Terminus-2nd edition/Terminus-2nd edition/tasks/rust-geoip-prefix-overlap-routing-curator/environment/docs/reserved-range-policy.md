# Reserved range policy

Drop records whose normalized CIDR falls entirely within these IPv4 networks before atlas row construction: 0.0.0.0/8, 10.0.0.0/8, 127.0.0.0/8, 169.254.0.0/16, 224.0.0.0/4. Count dropped rows in summary.reserved_dropped.
