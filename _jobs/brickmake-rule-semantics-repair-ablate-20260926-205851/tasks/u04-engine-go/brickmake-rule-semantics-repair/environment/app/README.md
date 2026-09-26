# brickmake

brickmake is a small, dependency-free build tool that reads GNU-style
makefiles. It is meant to be a drop-in replacement for GNU make 4.3 run as
`make -r -R` (no built-in rules, no built-in variables) for the part of the
makefile language described in `docs/`. For every supported construct,
brickmake prints the same recipe lines, the same messages and exits with
the same status as GNU make; the only intended difference is that its own
messages start with `brickmake:` instead of `make:`.

## Building

```
go build -o brickmake ./cmd/brickmake
go test ./...
```

Go 1.24, standard library only.

## Layout

| Path | Contents |
|---|---|
| `cmd/brickmake` | entry point |
| `internal/cli` | command-line options, variable setup, makefile lookup |
| `internal/parse` | logical lines, comments, conditionals, assignments, rule lines |
| `internal/db` | files, explicit rules, pattern rules, pattern-specific variables |
| `internal/vars` | variable definitions and sets |
| `internal/expand` | variable references, substitution references, functions, assignment semantics |
| `internal/engine` | implicit rule search, variable scopes, the update algorithm, recipes |
| `internal/text` | words and `%` patterns |
| `internal/diag` | message formatting |

## Documentation

- `docs/makefiles.md` - how makefiles are read
- `docs/variables.md` - flavors, appending, target- and pattern-specific variables
- `docs/rules.md` - explicit, static pattern and pattern rules; implicit rule search
- `docs/updating.md` - when targets are remade and what brickmake prints
- `docs/functions.md` - supported functions
- `docs/cli.md` - command line
