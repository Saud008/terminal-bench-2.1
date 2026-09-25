# Maildir flag letter order

Maildir filenames use an optional `:2,FLAGS` suffix on files in `cur/` and `new/`.

## Canonical flag letters

| Letter | Meaning | notmuch tag |
|--------|---------|-------------|
| F | flagged | flagged |
| S | seen (read) | seen |
| R | replied | replied |
| T | trashed | trashed |
| D | draft | draft |

## Parse rules

When reading a filename, split on the first `:2,` occurrence. The remainder is the flag set. Letters may appear in any order on disk; normalize to **FSRDT** order (only present letters) before comparing or writing.

## Write rules

When mirroring tags back to the maildir, build the flag suffix from tag presence:

- tag `flagged` → F
- tag `seen` → S
- tag `replied` → R
- tag `trashed` → T
- tag `draft` → D

Emit letters in **FSRDT** order. If no flags apply, omit the `:2,` suffix entirely.

Do not sort flag letters alphabetically.
