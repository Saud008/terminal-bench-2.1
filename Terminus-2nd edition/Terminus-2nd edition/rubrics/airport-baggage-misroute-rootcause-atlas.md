# Platform rubric — airport-baggage-misroute-rootcause-atlas

**Task folder:** tasks/airport-baggage-misroute-rootcause-atlas/

Agent latches hub topology with monotonic topology_revision, +2
Agent dedupes scan rows keeping highest relay_pass per bag_tag scan_seq, +3
Agent orders scan ledger by scan_minute then scan_seq ascending, +3
Agent selects belt target by highest priority not lexicographic belt_id, +3
Agent treats MCT feasible when gap equals min_connect_minutes, +3
Agent applies half-open outage windows excluding end_minute boundary, +3
Agent classifies CONNECTION_INFEASIBLE before BELT_UNMAPPED in taxonomy, +2
Agent excludes OUTAGE_SUPPRESSED rows from misroute_count totals, +3
Agent writes route lattice one row per normalized scan, +2
Agent exports audit_digest over sorted bag_tag scan_seq tuples, +2
Agent rebuilds bag-atlas with cargo release locked in test.sh, +2
Agent honors TB3_HUB_ROOT for hidden hub fixtures, +2
Agent honors TB3_MCT_MINUTES override during route-belts, +2
Agent leaves weight_decoy module off CLI hot path, +1
Agent sorts scan ledger by scan_minute only ignoring scan_seq tie-break, -3
Agent picks lowest belt_id when priorities collide, -3
Agent rejects MCT when gap equals published minimum connect minutes, -3
Agent suppresses scans at outage end_minute inclusive boundary, -2
Agent counts outage-suppressed rows inside misroute_count, -2
