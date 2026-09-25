# Include merge contract

The zonefrag ingest pipeline expands $INCLUDE directives inline while walking the master zone file top to bottom.

## Processing order

1. Start at manifest master (example example.com.zone).
2. Emit inline resource records from the master file in source order until a $INCLUDE directive.
3. When $INCLUDE appears, recursively expand the included file at that point, then resume master parsing after the directive.
4. Never prepend all include targets before master inline records.
5. Later units override earlier records on dedupe key (owner, class, type).

Relative include paths resolve from the including file directory. Track visited absolute paths to avoid cycles.

## processing_order field

The snapshot processing_order list must reflect the depth-first expansion sequence: master segments interleaved with include files at the point each $INCLUDE appeared, not a batch of includes followed by the master body.

## Exit codes

Missing manifest or master file: exit 2. Unrecoverable parse errors: exit 3.
