Implement the pestctl PEG precedence climb auditor on the working Rust baseline under /app. The tool ingests JSON grammar descriptors from a directory, writes a normalized rule-graph staging snapshot at /app/state/peg-rule-graph.json, runs precedence-climbing parse against token fixtures, and exports a span-attributed audit report to /app/output/span-audit.json with companion digest at /app/output/span-checksum.txt

Your work must satisfy every contract cited below. The src/decoy module is not on the ingest, climb, or audit export hot path and must not be edited for a correct export.

Build /app/bin/pestctl from the workspace root. Subcommands:

  pestctl ingest <grammars-dir>
  pestctl climb parse --input <tokens-json> [--graph <staging-path>]
  pestctl audit export

After ingest, /app/state/peg-rule-graph.json must list grammars in source filename order with rule names, explicit prec integers, decl_order metadata, left_recursive flags, and a climb_table array sorted for precedence climbing.

climb parse reads the staging graph and token JSON (tokens array plus grammar_id). It writes /app/state/parse-tree.json with span-tagged nodes. Rule precedence for climbing must follow /app/docs/rule-precedence-table.md: climb_table ordering uses explicit prec values only; declaration order must not override tighter-binding rules.

Left-recursive rules must follow /app/docs/atomic-boundary.md: atomic-wrapped inner patterns are matched before any left-recursive rule expansion on the same input position.

Whitespace handling must follow /app/docs/whitespace-contract.md: optional whitespace is consumed between sequence items, never after the configured sequence terminator token.

Negative predicates must follow /app/docs/negative-predicate.md: when the inner pattern partially matches but fails to complete, the input cursor must not advance.

audit export reads staging and parse-tree only. It writes /app/output/span-audit.json and derives /app/output/span-checksum.txt from the canonical span ledger in /app/docs/span-checksum-export.md. Recovered error nodes on backtrack paths must be included in the checksum ledger.

Bundled fixtures use /app/data/grammars and /app/data/inputs. Hidden verifier fixtures may supply additional grammars, token inputs, and TB3_PREC_BIAS precedence offset at runtime.
