# Yard SQLite contract

load-yard persists scenario rows into /app/state/yard.db.

## Tables

yard_meta stores scenario_id and billing_through. containers, gate_events, contracts, holds, closures, and tariffs mirror scenario JSON. staged_dwell is populated by run-dwell-ledger.

## Reset on load

load-yard clears prior yard rows and resets clock_pass. Operators must reload before changing scenarios.

## Query order

Gate events for dwell pairing read in insert order after chronological sort at load time.
