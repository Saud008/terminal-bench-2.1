# Pattern files

`.gitignore`, `.git/info/exclude` and the excludes file all use the same
syntax, the one described in gitignore(5). This page pins down the details
gleaner has to get right.

## Reading a file

- The file is split on LF. A UTF-8 byte order mark at the very start of the
  file is skipped. A CR directly before an LF, or at the end of an
  unterminated last line, is not part of the line.
- Lines are numbered from 1 and every line counts, whether or not it holds
  a pattern.
- An empty line holds no pattern. A line whose first character is `#` is a
  comment; `#` anywhere else is an ordinary character.
- Trailing spaces are removed unless they are escaped with a backslash.
  Only the space character counts: a trailing tab stays part of the
  pattern. `foo\ ` keeps its escaped space, and `foo\  ` becomes `foo\ `.
- A line that is empty after that holds no pattern.

## Parts of a pattern

- A leading `!` makes the pattern a negation: a path it matches is not
  ignored. To match a name that starts with `!` or `#`, put a backslash in
  front (`\!important`, `\#notes`). That backslash is an ordinary glob
  escape, so the pattern keeps it and `check` prints it.
- A trailing `/` makes the pattern match directories only. It is removed
  before the rest of these rules are applied.
- If what is left contains no `/`, it is matched against the last component
  of the path, at any depth below the directory of the pattern file.
- Otherwise (a `/` at the start or in the middle) it is matched against the
  path relative to the directory holding the pattern file, and a leading
  `/` only marks that. For `.git/info/exclude` and the excludes file that
  directory is the root. `doc/frotz` in `sub/.gitignore` matches
  `sub/doc/frotz` but not `sub/a/doc/frotz` or `doc/frotz`.

Matching is case-sensitive; `core.ignoreCase` is not consulted.

## Glob syntax

Patterns use git's wildmatch rules.

- `\x` matches `x` literally. A lone `\` at the end of a pattern makes it
  match nothing.
- `?` matches one character other than `/`; `*` matches any run of
  characters other than `/`.
- `[...]` matches one character from a set. It may hold single characters,
  ranges such as `a-z`, and the classes `[:alnum:]`, `[:alpha:]`,
  `[:blank:]`, `[:cntrl:]`, `[:digit:]`, `[:graph:]`, `[:lower:]`,
  `[:print:]`, `[:punct:]`, `[:space:]`, `[:upper:]` and `[:xdigit:]`.
  `[!...]` and `[^...]` match a character not in the set. A `]` right
  after the opening `[` (or after the `!`/`^`) is a member, as is a `-` at
  the start or the end. A backslash escapes the next character. A set never
  matches `/` in a pattern that contains a slash. An unknown class name or a
  missing closing `]` makes the whole pattern match nothing.
- In a pattern that contains a slash, a run of two or more `*` that makes up
  a whole component (preceded by the start of the pattern or `/`, followed
  by its end or `/`) may cross directories: a leading `**/` matches in every
  directory, including the top one; `/**/` matches zero or more directories,
  so `a/**/b` matches `a/b`, `a/x/b` and `a/x/y/b`; a trailing `/**`
  matches everything inside. Any other run of `*`, such as the one in
  `logs/202?**/raw` or `**z/q`, behaves like a single `*`.
