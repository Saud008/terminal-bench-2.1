# Vendor checksum contract

Each vendored crate may ship .cargo-checksum.json with a package field.

Compute package checksum as sha256 hex over UTF-8 bytes of newline-joined lines relative_path:sha256(file_bytes) sorted by relative_path ascending, excluding .cargo-checksum.json. When at least one file is present, append a single trailing newline to the payload before hashing.

Checksum mismatch when the vendor file package field is non-empty and differs from the computed digest.
