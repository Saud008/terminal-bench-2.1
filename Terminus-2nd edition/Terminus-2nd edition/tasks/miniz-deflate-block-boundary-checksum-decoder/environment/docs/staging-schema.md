# Staging snapshot: /app/state/decode-stage.json

Written on every successful decompress before the report is finalized. The report and staging snapshot must agree on Adler-32 and block metadata for the same run.

```json
{
  "input_path": "string absolute path",
  "block_count": "integer >= 1",
  "blocks": [
    {
      "index": "0-based integer",
      "block_type": "stored | fixed | dynamic",
      "final": "boolean",
      "uncompressed_len": "integer bytes emitted by this block",
      "block_checksum": "integer 0..65535 payload checksum for stored; 0 for Huffman blocks"
    }
  ],
  "window_size": 32768,
  "staging_adler": "integer lower 32 bits of running Adler before zlib trailer compare"
}
```

block_checksum for stored blocks is the low 16 bits of the sum of payload bytes only. For Huffman blocks the field is 0.

staging_adler must match an independent Adler-32 over all uncompressed bytes emitted across blocks, computed with every byte included.
