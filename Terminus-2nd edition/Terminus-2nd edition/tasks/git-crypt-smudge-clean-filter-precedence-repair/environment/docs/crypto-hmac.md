# Crypto blob and HMAC

## Encrypted blob layout (text)

```
GCRYPT1
KEY:<key_id>
DATA:<base64 ciphertext>
HMAC:<64 lowercase hex sha256>
```

Ciphertext is produced by XORing each plaintext byte with material[i mod 32] after converting plaintext to LF-only line endings.

## HMAC input

Compute SHA-256 over the LF-normalized plaintext bytes (CR stripped before LF, lone CR becomes LF). The HMAC line stores the hex digest. Smudge must verify HMAC only after LF normalization.

Computing HMAC on raw decrypted bytes without normalization causes false failures on CRLF fixtures.

## Pass-through

Plaintext blobs lack the GCRYPT1 header. Clean on non-filter paths must not add a header.

## Failure

Decrypt with wrong key, truncated DATA, or HMAC mismatch is a hard failure (exit 2 for smudge). No plaintext or partial staging output on failure.
