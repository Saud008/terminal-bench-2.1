# Where patterns come from

## Sources and precedence

For a path, these sources are consulted in order, and the first one that
has a matching pattern decides:

1. The `.gitignore` files in the path's parent directories, from the
   deepest one up to the root's. A deeper file overrides a shallower one.
2. `ROOT/.git/info/exclude`.
3. The excludes file (below).

Within one file the last matching pattern wins. A negation that wins means
"not ignored"; it does not let a lower-precedence source have a say.

A directory is judged by the files of its ancestors only; its own
`.gitignore` applies to what is inside it. Missing files, and paths that
are not regular files, are skipped silently.

## Excluded directories

Once a directory is excluded, nothing inside it can be re-included and the
`.gitignore` files inside it are not read. `list` does not enter it, and
`check` reports the pattern that excluded the outermost excluded parent for
every path below it. A negation only helps for a directory when the
directory itself is not excluded: `build/*` followed by `!build/keep.txt`
keeps `build/keep.txt`, while `build/` followed by `!build/keep.txt` does
not.

## The excludes file

The excludes file is `core.excludesFile` from `ROOT/.git/config`. When that
is not set, it is `$XDG_CONFIG_HOME/git/ignore` if `XDG_CONFIG_HOME` is set
and not empty, and `$HOME/.config/git/ignore` otherwise. A configured
value starting with `~/` (or a lone `~`) has that part replaced by `$HOME`.
A relative value is taken relative to the root.

`check` names the excludes file by that resulting string: the configured
value after `~` expansion, or the default path as built above.

## Config syntax

Only `ROOT/.git/config` is read (no system or global files, no includes).
The subset of git's syntax gleaner understands:

- `[section]` headers, and `[section "sub"]` / `[section.sub]` for
  subsections. Section and key names are case-insensitive, so `[Core]`
  with `ExcludesFile` sets `core.excludesfile`.
- `key = value` lines. The last assignment wins. A line ending in `\`
  continues on the next line.
- Values: surrounding whitespace is dropped, double quotes group (and keep
  inner whitespace), `\"`, `\\`, `\n`, `\t` and `\b` are escapes, and `#` or
  `;` outside quotes starts a comment.
