The gcrypt-filter driver at /app/bin/gcrypt-filter simulates git-crypt smudge and clean filters plus an encrypted-path export manifest, but filter precedence, submodule key resolution, LF normalization before HMAC, manifest specificity, and staging rollback on failed decrypt do not match the contracts under /app/docs/.

Repair the libraries under /app/lib/ so these subcommands behave per /app/docs/cli-reference.md:

clean reads plaintext on stdin and writes the index blob on stdout when --repo, --path, and optional --config are set. smudge reads the index blob on stdin and writes working-tree plaintext on stdout. export-manifest writes /app/output/encrypted-manifest.json per /app/docs/export-manifest-schema.md.

Filter attribute matching, clean versus smudge order, and pass-through rules are defined in /app/docs/gitattributes-rules.md and /app/docs/filter-pipeline.md. Key lookup for submodule worktrees is in /app/docs/submodule-keys.md. HMAC and blob layout are in /app/docs/crypto-hmac.md.

When --staging is passed to smudge, decrypted bytes land under /app/state/staging/ using the relative path; a failed decrypt must not leave a partial file there.

If --repo is missing, not a directory, or --path is empty, exit with status 1. Do not edit /app/docs/, /app/fixtures/, /app/config/filter.json, or files under /tests/.
