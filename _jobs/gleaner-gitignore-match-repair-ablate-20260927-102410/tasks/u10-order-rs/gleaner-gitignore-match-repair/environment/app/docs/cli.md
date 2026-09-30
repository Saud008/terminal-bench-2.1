# Command line

```
gleaner [--root DIR] list
gleaner [--root DIR] check [--] PATH...
gleaner --help
```

`--root DIR` (or `--root=DIR`) names the top of the work tree; the default
is the current directory. `ROOT/.git/config` and `ROOT/.git/info/exclude`
are read from there. gleaner never looks above the root.

Output is exactly what git prints for the same tree, as noted per command.
The rules git applies are written down in `patterns.md` and `sources.md`.

## list

Prints every file below the root that is not ignored, one per line,
relative to the root with `/` separators. The set and the order are those of
`git ls-files --others --exclude-standard` run at the top of a work tree in
which nothing is tracked.

- Only non-directories are printed. A symbolic link is printed like a file
  and never followed. Empty directories do not appear.
- An entry named `.git` is skipped at any depth, together with everything
  inside it.
- An ignored directory is not entered, so nothing below it is printed.
- Lines are sorted by the bytes of the whole relative path. `a-b` sorts
  before `a/b`, which sorts before `a0`.
- Names are printed as they are, without quoting. File names must be valid
  UTF-8.

Exit status 0.

## check

For each PATH, in the order given, prints one line in the format of
`git check-ignore -v -n`:

```
SOURCE:LINE:PATTERN<TAB>PATH
```

or, when no pattern decides the path,

```
::<TAB>PATH
```

- PATH is echoed as given. It is relative to the root and must consist of
  ordinary components: not empty, no leading or trailing `/`, no empty,
  `.` or `..` components. It does not need to exist.
- PATH is taken to be a directory when it exists as one (symbolic links are
  not followed); otherwise it is treated as a file.
- The deciding pattern is chosen as described in `sources.md`: if one of
  PATH's parent directories is excluded, it is the pattern that excluded
  the outermost such directory; otherwise it is the pattern that decides
  PATH itself, which may be a negation.
- SOURCE names the file the pattern came from: `.gitignore` for the root's
  file, `DIR/.gitignore` for a file in directory DIR (relative to the root),
  `.git/info/exclude`, or the excludes file spelled the way `sources.md`
  describes.
- LINE is the 1-based line number of the pattern in that file. Every line
  counts, including blank lines and comments.
- PATTERN is the line as written, after the unescaped trailing spaces are
  removed. A leading `!` and a trailing `/` are part of it.

Exit status: 0 if at least one PATH is ignored (its deciding pattern exists
and is not a negation), 1 if none is. This differs from git, which also
counts negated matches when `-v` is given.

## Errors

Usage errors, an invalid PATH and I/O errors print a message starting with
`gleaner: ` on standard error, print nothing on standard output, and exit
with status 2. All PATH arguments are validated before anything is printed.
