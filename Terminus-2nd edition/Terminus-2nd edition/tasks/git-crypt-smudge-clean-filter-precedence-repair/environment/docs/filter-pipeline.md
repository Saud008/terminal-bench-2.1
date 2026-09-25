# Filter pipeline

## clean (working tree to index)

1. Read all stdin bytes as plaintext.
2. Resolve the winning filter attribute for --path per /app/docs/gitattributes-rules.md.
3. If filter is not gcrypt, write plaintext unchanged to stdout and stop.
4. Otherwise load key material per /app/docs/submodule-keys.md, encrypt per /app/docs/crypto-hmac.md, write blob to stdout.

Encrypting before step 2 is incorrect and breaks pass-through paths that share a prefix with encrypted globs.

## smudge (index to working tree)

1. Read all stdin bytes as a blob.
2. If the blob does not begin with the GCRYPT1 header, treat it as plaintext pass-through: copy to stdout and optional staging unchanged.
3. Resolve filter for --path. If filter is not gcrypt but the blob is encrypted, fail with exit code 2.
4. Decrypt blob, normalize CRLF to LF on the decrypted bytes before HMAC verification per /app/docs/crypto-hmac.md.
5. On success write plaintext to stdout and, when --staging is set, atomically to /app/state/staging/RELPATH.
6. On decrypt or HMAC failure, remove any partial staging file for RELPATH and exit 2.

## export-manifest

Manifest collection must use the same attribute precedence as clean/smudge. Listing every file under a directory glob without evaluating the winning rule per path is incorrect.
