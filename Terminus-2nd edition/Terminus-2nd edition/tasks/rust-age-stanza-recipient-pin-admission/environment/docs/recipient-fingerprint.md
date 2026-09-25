# Recipient fingerprint

Each parsed stanza yields a fingerprint used for pin matching.

## Preimage

Let `TYPE` be the stanza type with ASCII letters uppercased (digits and punctuation unchanged). Let `args` be the argument strings **exactly as they appear** on the stanza line (no Base64 re-encode).

Preimage bytes:

```
TYPE\n
arg1\n
arg2\n
...
```

Fingerprint = lowercase hex encoding of SHA-256(preimage).

## Notes

- Argument whitespace splitting is on ASCII spaces only; empty args are not permitted.
- Lowercase or mixed-case types on the wire still fingerprint with the uppercased `TYPE` string above.
- Do not include the `->` marker or trailing ciphertext in the preimage.
