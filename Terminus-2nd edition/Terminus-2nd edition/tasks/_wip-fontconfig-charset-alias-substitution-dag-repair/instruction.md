Implement the fc-alias-check compile-and-resolve governor on the working Rust baseline under /app/crates/. The tool compiles fontconfig-style XML into a normalized staging snapshot at /app/state/fc-compiled.json, validates alias graphs, and exports charset resolution reports under /app/output/.

Your work must satisfy every contract cited below. The src/decoy module is not on the compile or resolve export hot path and must not be edited for a correct export.

Build fc-alias-check from the workspace root. Subcommands:

  fc-alias-check compile --config <path> [--inject <fragment>]
  fc-alias-check resolve --charset <name> --family <query> --export <path>
  fc-alias-check check --config <path> [--inject <fragment>]

After compile, /app/state/fc-compiled.json must list merged charsets in source declaration order with compile_meta per staging-compiled.md. resolve reads staging only and never re-parses XML from the original config paths.

Charset registry lookup must follow charset-registry.md: queries use the full name attribute exactly. Basename extraction or short-name indexing is wrong when multiple charsets share a revision prefix.

Alias expansion must follow alias-dag.md: walk every hop until a terminal charset node is reached. Single-hop truncation is incorrect.

Substitute preference ordering must follow substitute-preferences.md: prefer entries export in XML declaration order without reversal.

Bitmap and outline rejection must follow font-reject-rules.md: reject-outline and reject_bitmap are independent flags affecting font_kinds_allowed.

Encoding propagation must follow charset-registry.md and alias-dag.md: resolved encoding comes from the terminal charset node, not the query charset node.

Cycle detection must follow alias-dag.md and cli-reference.md: check exits with status 2 when a cycle is present.

Bundled fixtures live under /app/fixtures/. Hidden verifier fixtures may supply additional config trees under /opt/verifier-fixtures/fc-configs/ at runtime.

Rebuild with CARGO_NET_OFFLINE=true after Rust edits. The image ships a prebuilt binary at /usr/local/bin/fc-alias-check. Do not modify /app/docs/, anything under /app/fixtures/, or anything under /tests/.
