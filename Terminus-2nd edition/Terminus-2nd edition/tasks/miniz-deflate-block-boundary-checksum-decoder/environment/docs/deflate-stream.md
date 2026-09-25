# DEFLATE stream contract (zlib wrapper)

Public inputs are zlib-wrapped DEFLATE (RFC 1950). CMF/FLG must indicate method 8 and a valid FCHECK. The deflate bitstream follows immediately after the two-byte header; the stream ends with a big-endian Adler-32 over the **uncompressed** payload.

## Block types

Each block begins with a 3-bit header: final (1 bit) then type (2 bits). Type 0 is stored, 1 fixed Huffman, 2 dynamic Huffman.

### Stored blocks (type 0)

After bit alignment to a byte boundary, read LEN and NLEN as little-endian u16. LEN must equal bitwise NOT of NLEN. The LEN field counts **only** the uncompressed bytes that follow; it does not include the four header bytes.

The stored checksum used internally for staging is the low 16 bits of the sum of all bytes in the block **payload** (not including LEN/NLEN). Staging block_checksum must equal that payload sum for stored blocks.

An empty stored block (LEN=0) is valid and must be consumed even when more blocks follow. Do not treat LEN=0 as end-of-stream unless the final bit is set on that block.

### Dynamic Huffman (type 2)

Code length order for the first tree follows RFC 1951 section 3.2.7 exactly:

16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15

Rebuild literal/length and distance trees from the decoded length sequence, then decode symbols until end-of-block (256).

### Sliding window

Back-reference copies use a 32 KiB ring buffer. Distance and length may reference bytes produced in an earlier block; indices wrap modulo 32768 when the copy crosses the window edge.

## Adler-32

Update Adler-32 incrementally as uncompressed bytes are emitted. Every emitted byte participates exactly once, including the last byte of each stored or Huffman block, before comparing to the zlib trailer.

## Chained fixtures

Some inputs chain stored then dynamic blocks with an empty stored block between payload sections. The decoder must process every block in order and record block_count in staging.
