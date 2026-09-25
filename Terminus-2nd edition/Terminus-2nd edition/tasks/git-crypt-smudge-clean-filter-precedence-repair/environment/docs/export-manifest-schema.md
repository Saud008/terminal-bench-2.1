# Export manifest schema

Output JSON object:

- manifest_version: integer, always 1
- repo_root: absolute path string of --repo
- entries: array sorted by path ascending (C locale)

Each entry object:

- path: relative POSIX path using forward slashes
- filter: string, always gcrypt for listed rows
- key_id: eight hex chars from the repo key file
- specificity: integer score from /app/docs/gitattributes-rules.md for the winning rule

Only paths that exist as files under the repo fixture tree and whose winning attribute is filter=gcrypt appear. Paths excluded by a higher-precedence -filter rule must be omitted even if they sit under an encrypted directory glob.

Tracked fixture walk roots are listed in /app/docs/fixture-catalog.md.
