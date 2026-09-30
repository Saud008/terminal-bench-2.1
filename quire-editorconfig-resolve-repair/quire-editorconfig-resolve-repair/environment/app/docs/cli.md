# quire command line

quire is a drop-in replacement for the `editorconfig` program of EditorConfig
C Core 0.12.6 (Debian bookworm package `editorconfig`, version 0.12.6-0.1).
Given the same arguments, EditorConfig files and standard input, it writes the
same bytes to standard output and standard error and exits with the same
status. The one difference is that the usage text names the program the way
it was invoked.

## Synopsis

    quire [OPTIONS] FILEPATH1 [FILEPATH2 FILEPATH3 ...]

Options are only recognised before the first file path. The first argument
that is not one of the options below starts the path list, and every argument
after it is a path, even one that looks like an option.

| Option | Meaning |
|---|---|
| `-f NAME` | read EditorConfig files named `NAME` instead of `.editorconfig` |
| `-b VERSION` | resolve the way core version `VERSION` would (see `resolution.md`) |
| `-h`, `--help` | print the version line and the usage text to stdout, exit 0 |
| `-v`, `--version` | print `EditorConfig C Core Version 0.12.6` to stdout, exit 0 |

Without any argument the version line and the usage text go to stderr and the
exit status is 1. With options but no file path (a trailing `-f` or `-b`
without its value included) the usage text goes to stderr, exit status 1.

### `-b VERSION`

`VERSION` is split at dots; empty components are skipped, so `0..10` means
0.10. Each component is read like C `strtol` in base 10: optional leading
whitespace and sign, then the leading digits, 0 when there are none. The
components are major, minor and patch; a negative component counts as not
given. With more than three components quire prints
`Invalid version number: VERSION` to stderr and exits with status 1 before
looking at any file.

Components that were not given are 0, and 0.0.0 means the current version
0.12.6. `-b` may be given more than once; a later one only overwrites the
components it contains.

## File paths

Every file path must be absolute, i.e. start with `/`. Paths are used exactly
as written: `.` and `..` are not cleaned up, symbolic links are not followed
and the file does not have to exist.

A path argument `-` stands for the file paths read from standard input, one
per line, until the end of input. Whitespace around each line is removed and
blank lines are skipped. Once standard input is exhausted, a further `-`
yields no paths.

## Output

For every file, quire prints one `name=value` line per property, in the order
given in `resolution.md`. A file with no properties prints nothing.

A header line `[PATH]` precedes a file's properties when more than one path
argument was given, and always for a path read from standard input, even when
`-` is the only argument. The header is printed before the file is resolved,
so it also appears when resolving that file fails.

## Errors

quire stops at the first file that cannot be resolved; everything printed for
earlier files stays printed. It then writes one line to stderr and exits with
status 1. The checks are made in this order:

| Situation | Message |
|---|---|
| `-b` asks for a version newer than 0.12.6 | `Required version is greater than the current version.` |
| the path does not start with `/` | `Input file must be a full path name.` |
| an EditorConfig file has a syntax error | `Failed to parse file.:LINE "FILE"` |

`LINE` is the number of the first line with a syntax error in that file (see
`format.md`) and `FILE` is the EditorConfig file's path as quire built it
(see `resolution.md`). EditorConfig files that cannot be opened are skipped
without a message. When every file resolves, the exit status is 0.
