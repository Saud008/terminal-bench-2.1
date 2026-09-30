Our pre-commit hooks and editor plugins ask quire (source in `/app`) which EditorConfig settings apply to a file, and since the rewrite it keeps disagreeing with the `editorconfig` tool it replaced. What people have reported so far:

- a `[scripts/**]` section in `/repo/.editorconfig` also applies to `/repo/tools/scripts/deploy.sh`
- `indent_style = tab` on its own no longer gives `indent_size=tab`, and `-b 0.8` is refused as too new
- when the checkout lives in a folder like `/srv/work/[wip] shop`, nothing from its `.editorconfig` applies
- `echo /repo/app.py | quire -` prints the properties without the `[/repo/app.py]` line

That's probably not everything. quire is meant to be a drop-in for `editorconfig` from EditorConfig C Core 0.12.6 (the Debian bookworm package): same output, same errors, same exit codes, apart from the program name in the usage text. The docs in `/app/docs` are the spec, so make quire follow them. It'll be checked against other trees, paths and options than the ones above.

Keep it plain Go on the standard library only (no modules, no cgo or `unsafe`, no running other programs), keep the command line from `/app/docs/cli.md`, and building `/app/cmd/quire` with a plain `go build` from `/app` has to keep working.
