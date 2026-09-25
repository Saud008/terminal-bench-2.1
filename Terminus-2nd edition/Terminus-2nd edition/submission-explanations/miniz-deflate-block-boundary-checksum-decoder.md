# Submission explanations — miniz-deflate-block-boundary-checksum-decoder

**Task folder:** tasks/miniz-deflate-block-boundary-checksum-decoder/
**Platform form only** — not in upload zip.

## Difficulty Explanation

The minizdecode Rust crate must inflate zlib-wrapped DEFLATE streams while emitting a staging snapshot and JSON report that stay aligned on Adler-32 and per-block metadata. Failures are spread across stream block iteration, empty stored blocks in chained inputs, dynamic Huffman table rebuild order, sliding-window copies that cross block edges, and trailer checksum comparison after decode. Agents who patch one module often pass hello or single-block fixtures yet still truncate chained stored streams, mis-record staging block_checksum on payload bytes, or return the wrong exit code when the zlib trailer disagrees with decoded output. Hidden streams under /opt/verifier-fixtures and TB3 seed traps require all layers to cooperate, not a single obvious edit in one file.

## Solution Explanation

The oracle copies golden Rust modules into minizdecode for adler accumulation, stored-block handling, fixed and dynamic Huffman decode, sliding-window copies, stream block-loop semantics, and export/report writing, then rebuilds with cargo and installs the binary. The central insight is that the stream driver must continue past zero-length non-final stored blocks instead of stopping early on empty middle blocks in chained inputs. Adler must accumulate over every emitted byte across block boundaries before comparing the zlib trailer, and staging must record sequential indexes, correct final flags, and payload-only stored checksums. Export writes output and report, then returns checksum mismatch as exit status 2 when computed_adler32 disagrees with the trailer. Partial fixes to window or Huffman alone leave staging_adler or block metadata inconsistent with the report contract.

## Verification Explanation

test.sh rebuilds minizdecode before pytest. Tests invoke the minizdecode decompress subcommand as a subprocess and compare inflated bytes to reference_inflate_zlib built from Python zlib as an independent reference. Staging and report JSON are parsed directly with assertions for input_path, sequential block indexes, final flags, stored payload checksums, and zero Huffman block_checksum fields. Hidden streams under /opt/verifier-fixtures/streams exercise chained stored blocks and compressed LZ77 chains without bundled fixture hints. A dedicated test corrupts the zlib Adler trailer and expects exit code 2 per the CLI contract. Another test exercises missing input, truncated zlib, invalid header check, reserved DEFLATE block type, and truncated stored-block payloads, each expecting exit code 1 for I/O or format errors. Oracle installs all golden modules and rebuilds; NOP on the shipped broken image scores zero.
