# Decompress report: /app/output/decompress-report.json

```json
{
  "input_path": "string",
  "output_path": "string",
  "uncompressed_len": "integer",
  "adler32": "integer expected from zlib trailer",
  "computed_adler32": "integer from decoder accumulation",
  "block_count": "integer",
  "ok": "boolean true when computed_adler32 matches trailer and length matches output file"
}
```

computed_adler32 must equal staging_adler in decode-stage.json for the same run.
