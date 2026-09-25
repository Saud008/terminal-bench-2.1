# vaultaud CLI surface

Binary path: `/app/bin/vaultaud`

## audit

```
vaultaud audit --transcript-dir DIR --config-dir DIR --staging PATH
```

Aliases: `collect`, `ingest`.

## rollup

```
vaultaud rollup --staging PATH --atlas PATH
```

Aliases: `publish`, `export`.

Both subcommands exit non-zero with a message on stderr for any fatal input error.
