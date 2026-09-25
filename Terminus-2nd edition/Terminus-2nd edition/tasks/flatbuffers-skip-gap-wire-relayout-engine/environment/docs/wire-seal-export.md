# Wire seal export

The attestation file /app/output/wire-seal.txt contains one lowercase hexadecimal SHA-256 digest followed by a newline.

The digest must be computed over the final relayout.wire bytes after the gap restoration pass completes.

Computing the digest on the relayout buffer before gap spans are restored into the output produces a seal that does not match the on-disk relayout.wire file and is incorrect.

The canonical digest uses standard SHA-256 over the full relayout.wire byte sequence with no additional salt or metadata.
