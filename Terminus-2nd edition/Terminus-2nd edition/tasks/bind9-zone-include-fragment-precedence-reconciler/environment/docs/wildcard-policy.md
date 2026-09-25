# Wildcard apex overlap policy

After all fragments merge, scan the final effective record set for wildcard apex conflicts.

## Detection scope

Compare every wildcard owner (*.origin suffix) against apex names (@ or the zone origin label) across the merged zone, including records contributed by $INCLUDE fragments.

Single-file scans are insufficient. A wildcard in fragments/ must be checked against apex records defined in the master file and vice versa.

## Conflict reporting

Each conflict is an object with wildcard, apex, and type fields. The snapshot wildcard_conflicts array must list every overlap. verify fails when the array is non-empty.

## Covered apex forms

Treat @ and the bare origin (example.com. without trailing dot normalization) as apex equivalents for overlap detection when the manifest origin is example.com.

## Apex record types

Only A and AAAA record types count as apex conflicts. MX, TXT, SOA, and other apex owner types do not produce wildcard_conflicts entries even when a wildcard owner overlaps the same origin.
