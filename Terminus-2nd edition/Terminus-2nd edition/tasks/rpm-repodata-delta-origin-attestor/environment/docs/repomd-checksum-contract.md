# Repomd checksum contract

Each repomd data entry includes a checksum element with a type attribute and hex digest text. Verification must read the metadata file referenced by location href relative to the repository root and hash the raw file bytes.

When type is sha256, compute SHA-256 of the file and compare to the digest in repomd.xml. When type is sha, compute SHA-1. Do not substitute algorithms across types.

Both primary and modules data entries must be verified during ingest. Record checksum_ok as true only when every present data entry passes verification.
