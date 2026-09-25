# Decode pipeline

1. ingest: validate zlib header, strip wrapper for bitstream reader
2. stream: iterate DEFLATE blocks, emit bytes into sliding window
3. staging: persist block metadata to /app/state/decode-stage.json before trailer check
4. export: write output bytes and decompress-report.json

Fixed Huffman (type 1) may be handled by huffman_static.rs for diagnostics; production streams in fixtures rely on stored and dynamic blocks. Cross-block back-references are resolved in window.rs against the ring buffer maintained in stream.rs.
