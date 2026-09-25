# gitattributes rules

Each repo root may contain a .gitattributes file. Lines are trimmed; empty lines and lines starting with # are ignored.

## Pattern forms

- Literal path: secret/plain.txt
- Glob: secret/**, *.key, sub/module/secret/**
- Negation: prefix a pattern with ! to unset a macro. Example: !public/readme.txt -filter clears filter on that path.

## Macro attributes

filter=gcrypt marks a path for the gcrypt clean/smudge driver. -filter or filter= clears encryption for that path.

## Precedence

For a relative path RELPATH inside ROOT:

1. Collect every non-negated rule whose pattern matches RELPATH using git-style pathspec rules: ** matches across slashes, * matches within one path segment, ? matches one character.
2. Score each match: literal paths score 10000 plus byte length; globs score 100 times the number of literal characters plus 10 times slash count.
3. The highest score wins. On a tie, the later line in file order wins.
4. If the winning line sets filter=gcrypt, the path is encrypted. If the winning line clears filter or sets no filter attribute, the path is plaintext pass-through.

Nested .gitattributes under subdirectories are not used; only the file at ROOT/.gitattributes applies.

## Submodule note

When --repo points at a submodule worktree (for example fixtures/repos/submod-child), key material still resolves from that worktree root, not the parent checkout. See /app/docs/submodule-keys.md.
