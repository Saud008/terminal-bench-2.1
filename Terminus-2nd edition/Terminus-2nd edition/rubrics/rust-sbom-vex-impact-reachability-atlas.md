# Platform rubric — rust-sbom-vex-impact-reachability-atlas

**Task folder:** tasks/rust-sbom-vex-impact-reachability-atlas/

Agent normalizes PKG:CARGO package identities to canonical lowercase purls before snapshot capture, +3
Agent computes staging_digest over sorted packages edges and vex without reversing hash bytes, +3
Agent applies VEX not_affected precedence over fixed and affected for the same product and vuln, +3
Agent ignores expired not_affected statements when expiry equals current UTC instant, +2
Agent expands runtime reachability transitively across dependency edges not one hop only, +3
Agent ignores dev edge_kind when computing binary reachability closure, +2
Agent sorts impact rows by binary then package_purl then vuln_id before export_digest, +2
Agent attaches waiver evidence only for active not_affected or fixed winning statements, +2
Agent reads waiver-snapshot.json only during rollup without reopening capture bundle path, +2
Agent keeps run_seq stable when bundle fingerprint unchanged across repeated capture, +1
Agent emits exposure ledger with single trailing newline per exposure-ledger-schema, +1
Agent mishandles PKG scheme case leaving uppercase type segment in norm_purl, -3
Agent uses direct dependency hops only missing transitive tokenhash reachability, -3
Agent ranks fixed VEX above not_affected for competing statements, -3
Agent treats expired waiver as still active using inclusive expiry comparison, -3
Agent includes dev-only dependency paths in runtime reachability impacts, -3
Agent sorts impacts by vuln_id only breaking deterministic export_digest contract, -2
Agent hashes reversed snapshot body bytes producing wrong staging_digest, -2
