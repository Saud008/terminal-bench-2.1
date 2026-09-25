# CLI errors

Exit codes:

- 0: success
- 2: missing catalog, missing required flags, unknown command
- 3: invalid catalog JSON or filter pipeline error

filter requires --catalog and --output. --workers must be a positive integer.
