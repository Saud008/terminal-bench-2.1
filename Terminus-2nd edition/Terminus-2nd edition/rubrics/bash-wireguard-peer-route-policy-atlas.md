# Platform rubric — bash-wireguard-peer-route-policy-atlas

**Task folder:** tasks/bash-wireguard-peer-route-policy-atlas/

Agent implements wgpatlas ingest loading site manifest WireGuard confs routes and site-policy, +3
Agent parses AllowedIPs as full comma-separated CIDR list per WireGuard peer stanza, +3
Agent detects allowed-IP overlap using proper ip_network overlap math not string prefix, +3
Agent applies endpoint_precedence lower metric wins over wg conf Endpoint field, +2
Agent detects cross-interface route table_id conflicts from routes JSON bundles, +3
Agent excludes disabled_peers from staging overlap detection and export peers array, +3
Agent materializes wgpatlas-workspace.json with workspace_fingerprint including overlaps and disabled_skipped, +2
Agent exports atlas JSON with peers sorted by public_key and audit_digest over peers overlaps conflicts, +3
Agent honors TB3_SITE_ROOT for hidden site bundles during ingest analyze export, +2
Agent fixes only parse_wg_conf while leaving cidr overlap on broken prefix compare, -3
Agent patches decoy mesh_rank_helper onto ingest or export hot path, -3
Agent includes disabled peers in export atlas or overlap edges, -5
Agent sorts export peers by peer_id name instead of public_key ascending, -3
Agent reports route conflicts only within same interface ignoring cross-interface table_id, -3
