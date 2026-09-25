# Platform rubric — fishery-quota-landing-reconciliation-map

**Task folder:** tasks/fishery-quota-landing-reconciliation-map/

Agent resolves regional species aliases to canonical quota keys before conversion, +3
Agent multiplies product weight by live-weight factor instead of dividing, +3
Agent treats permit valid_until date as inclusive when checking landing timestamps, +3
Agent rejects landings whose coordinates fall inside closed-area bounding boxes, +3
Agent adds prior-season carryover kilograms to allocated quota totals, +2
Agent sums landed live weight only for accepted JSONL ledger rows in atlas export, +3
Agent writes quota atlas species rows sorted by species code ascending, +2
Agent matches atlas output to independent reference reconciliation math, +3
Agent uppercases raw species codes without walking alias tables, -3
Agent divides product weight by conversion factor producing under-counted live kilograms, -3
Agent excludes landings on the permit expiry date due to strict less-than bound, -3
Agent counts rejected closed-area landings toward species landed totals, -3
Agent omits carryover pool from allocated_kg leaving false over-quota readings, -2
