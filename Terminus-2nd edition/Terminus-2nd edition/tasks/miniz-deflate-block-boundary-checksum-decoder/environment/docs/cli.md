# minizdecode CLI

Binary: minizdecode (installed to PATH after cargo build).

Subcommand decompress:

- --input PATH  zlib file to read
- --output PATH raw inflated bytes to write
- --report PATH JSON report path (typically /app/output/decompress-report.json)
- --staging PATH staging snapshot (typically /app/state/decode-stage.json)

Exit 0 on success, 1 on I/O or format error, 2 on checksum mismatch after decode.

Idempotent: repeated runs on unchanged input produce identical output bytes and JSON fields.
