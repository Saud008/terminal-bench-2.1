# SOA serial bump policy

Reload compiles pass --reload to ingest and compile. On reload, bump the authoritative SOA serial by exactly one.

## Authoritative SOA source

The serial used for reload bumping must come from the SOA record in the master zone file named by manifest master, not from SOA records appearing only in included fragments.

Fragment SOA records are ignored for reload serial policy even if they appear earlier in processing_order.

## Output fields

Snapshot soa_serial holds the final serial after optional bump. soa_source must name the master-relative path (example example.com.zone) when reload uses master SOA.

When reload is false, preserve the master SOA serial without incrementing.

## Reload example

Master SOA serial 2026052105 with --reload yields 2026052106 regardless of decoy fragment SOA values.
