# Platform rubric — bird-aspath-filter-peer-cutover-witness

**Task folder:** tasks/bird-aspath-filter-peer-cutover-witness/

Agent orders peers by wave_rank then asn then peer_id for peer_order and evaluation, +3
Agent replaces group filters with same filter_id from the peer and sorts by priority desc then filter_id, +3
Agent matches origin on the last ASN and transit excluding origin and exact element-wise as_path, +3
Agent rewrites communities in lexicographic key order and never rewrites ASN 0 or 65535 communities, +3
Agent clamps accepted route med with the lesser of med and med_ceiling and leaves denied routes unchanged, +3
Agent restores rib_after from the pre-evaluation checkpoint on critical-prefix deny abort and stops the wave, +3
Agent seals the report from ledger peer_order and row order without re-sorting during seal, +2
Agent appends TB3_PEER_SALT to peer and RIB peer_id values before cutover evaluation, +2
Agent rebuilds and installs bgpcut after patching pwcore Go modules, +2
Agent leaves decoy packages off the cutover hot path and does not edit docs fixtures or config, +1
Agent sorts peers by peer_id alone ignoring wave_rank and asn, -3
Agent concatenates group and peer filters without replacing shared filter_id entries, -3
Agent matches origin against the first ASN or treats transit as any-path membership including origin, -3
Agent rewrites well-known communities or clamps med with max instead of min, -3
Agent sets wave_aborted on critical deny but leaves earlier accept mutations in rib_after, -3
Agent re-sorts peer_order or digest rows during SealReport instead of trusting the ledger, -2
Agent patches only one pwcore module while wave order inheritance rewrite MED or abort stay wrong, -2
