# Platform rubric — fontconfig-charset-alias-substitution-dag-governor

**Task folder:** tasks/fontconfig-charset-alias-substitution-dag-governor/

Agent writes /app/state/fc-compiled.json at compile with charset declaration order preserved, +3
Agent bumps /app/state/compile-seq.txt on every successful compile, +2
Agent computes graph_hash from merged config canonical JSON plus inject path, +3
Agent resolves charset queries by full registry name not basename or short tag, +3
Agent walks alias chains to terminal charset nodes with every intermediate hop, +3
Agent exports substitute prefer lists in XML declaration order without reversal, +2
Agent propagates encoding from terminal charset not the query charset node, +2
Agent keeps reject_bitmap and reject_outline independent in font_kinds_allowed, +2
Agent reads staging only in resolve without re-parsing fixture XML, +3
Agent detects alias cycles and exits check with status 2, +2
Agent leaves src/decoy off compile and resolve export hot paths, +1
Agent collapses duplicate short charset tags into one registry entry, -3
Agent truncates alias expansion after a single hop, -3
Agent reverses prefer list order during export, -2
Agent copies reject_bitmap into reject_outline, -2
Agent hashes only base config path ignoring inject overlay content, -3
Agent re-parses XML during resolve instead of reading staging, -3
Agent skips cycle detection and returns check exit 0 on cyclic graphs, -3
