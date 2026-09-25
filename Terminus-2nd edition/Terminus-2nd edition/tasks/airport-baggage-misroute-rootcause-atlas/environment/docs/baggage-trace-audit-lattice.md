# baggage-trace-audit-lattice.md

Five derivation layers for misroute root-cause classification:

1. Scan trace normalization — dedupe by bag_tag and scan_seq, sequence by scan_minute then scan_seq.
2. Belt binding — map scan belt_id and station_code to target flight using belt_weight tie-break.
3. Connection matrix — evaluate inbound-to-outbound MCT gap against published min_connect_minutes.
4. Outage mask — half-open station outage windows suppress scans without counting as misroutes.
5. Cause class — apply OUTAGE_SUPPRESSED, CONNECTION_INFEASIBLE, BELT_UNMAPPED, ROUTED_OK stack.

Layers 1-4 produce route lattice rows; layer 5 aggregates misroute_count excluding suppressed rows.
