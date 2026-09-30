# quire

quire answers which EditorConfig properties apply to a file. It replaces the
`editorconfig` program from EditorConfig C Core in our hooks and editor
integrations.

    go build ./cmd/quire
    ./quire /abs/path/to/file.go

Layout:

| Path | Contents |
|---|---|
| `cmd/quire` | entry point |
| `internal/cli` | argument handling, path input, output |
| `internal/resolve` | EditorConfig file discovery and section matching |
| `internal/glob` | section glob to regular expression translation |
| `internal/ini` | EditorConfig file parser |
| `internal/props` | property store, value case and derived indentation |
| `internal/version` | core and `-b` versions |
| `internal/ctext` | C character and number rules |
| `docs` | specification |
