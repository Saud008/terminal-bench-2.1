Implement the miniz-style zlib decompressor under /app/crates/minizdecode so it inflates public streams under /app/fixtures/streams/ and writes raw bytes plus a JSON report. The decoder must handle DEFLATE block boundaries, dynamic Huffman rebuild order, Adler-32 accumulation across blocks, sliding-window copies that span block edges, and zero-length stored blocks that appear before the stream end marker on chained inputs.

Run minizdecode decompress with --input pointing at a .zlib file, --output for inflated bytes, --report for /app/output/decompress-report.json, and --staging for /app/state/decode-stage.json. Block layout, staging snapshot fields, report schema, and CLI flags are defined in /app/docs/deflate-stream.md, /app/docs/staging-schema.md, /app/docs/report-schema.md, and /app/docs/cli.md. Re-running decompress on the same input must yield byte-identical output and report.

Do not edit files under /app/fixtures/streams/, /app/docs/, or /tests.
