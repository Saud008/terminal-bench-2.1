# Platform rubric — rust-peg-precedence-climb-auditor

**Task folder:** tasks/rust-peg-precedence-climb-auditor/

Agent sorts climb_table by descending explicit prec not declaration order, +3
Agent uses climb_table prec values for operator binding during parse, +3
Agent matches atomic inner patterns before left-recursive expansion at same cursor, +3
Agent consumes whitespace only between sequence items not after terminators, +2
Agent keeps cursor fixed when negative predicate inner partially overlaps token, +2
Agent includes recovered error_recovery nodes in span audit ledger, +3
Agent derives span checksum from full audit JSON including recovered spans, +2
Agent rebuilds pestctl after editing grammar climb or export crates, +2
Agent reads rule graph staging during climb parse not raw grammar files, +2
Agent edits decoy merge module expecting export fix, -3
Agent patches only climb_table ingest while leaving op_prec on rank, -3
Agent expands left-recursive rules before atomic boundary check, -2
Agent commits input position on partial neg pred inner match, -2
Agent omits recovered nodes from span checksum ledger, -3
