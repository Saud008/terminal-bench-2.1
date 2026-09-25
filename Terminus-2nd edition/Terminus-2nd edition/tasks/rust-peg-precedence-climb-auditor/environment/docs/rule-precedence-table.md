# Rule precedence table

The climb_table array in /app/state/peg-rule-graph.json is authoritative for operator binding strength during pestctl climb parse.

Each climb_table row carries rule (grammar_id::rule_name), prec copied from the grammar rule, rank as the zero-based climb order, and left_recursive copied from the rule.

Rows must be sorted by descending prec. When two rules share the same prec, tie-break by ascending rule name lexicographically.

Declaration order (decl_order) is ingest metadata only. It must never determine climb rank or operator precedence during parse.

The rank field after sorting must equal the row index in climb_table.
