# OpenSSH known_hosts line format

This task uses the standard OpenSSH `known_hosts` line grammar:

```text
[marker ]host[,host...] key-type base64-key [comment]
```

## Markers

- `@revoked` — the key is revoked and must not be trusted.
- `@cert-authority` — following keys are certificate authorities for the listed hosts.

Markers are literal tokens at the beginning of the line.

## Host fields

Plain entries list one or more host patterns separated by commas. Non-default SSH ports use bracketed hostnames:

```text
[example.com]:2222
```

Hashed entries replace the host list with a single token:

```text
|1|base64-salt|base64-hash
```

The leading `1` is the hash version mandated by OpenSSH.

## Key types

Common key types include `ssh-ed25519`, `ssh-rsa`, and `ecdsa-sha2-nistp256`. The normalizer treats the key type as an opaque ASCII token.

## Comments

Any text after the key blob separated by whitespace is a comment. Comments participate in duplicate merge tie-breaking but are otherwise preserved verbatim.

## Legacy sort helper

`/app/lib/decoy/kh_sort_legacy.sh` is a historical helper that sorted records by key blob. Export ordering is defined in `/app/docs/normalize-contract.md` and implemented in `kh_merge.sh`; do not treat the decoy helper as the export sort source.
