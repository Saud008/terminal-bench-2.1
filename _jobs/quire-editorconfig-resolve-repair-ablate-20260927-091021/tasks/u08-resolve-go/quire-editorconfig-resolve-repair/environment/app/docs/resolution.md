# Resolving a file

## EditorConfig files read

For the file `/a/b/c.txt` quire reads `/.editorconfig`, `/a/.editorconfig`
and `/a/b/.editorconfig`, in that order: one EditorConfig file per `/` in the
path, taking the directory as the path cut at that `/`, farthest first. With
`-f NAME` the files are named `NAME` instead. Files that cannot be opened are
skipped.

## Collecting properties

Every property in a section whose glob (see `globs.md`) matches the file path
is recorded:

- Property names are case-insensitive. They are recorded and printed in
  lowercase.
- Recording a name that has already been recorded replaces its value and
  keeps its position. A new name is added at the end.

Because files are read farthest first and top to bottom, later lines and
nearer files win, and properties are printed in the order in which their
names were first recorded.

### root

A property named `root` with the value `true` in the preamble of an
EditorConfig file (both compared case-insensitively) discards everything
recorded so far, i.e. everything that came from the files farther up. Order
starts afresh from there. A preamble `root` with another value has no effect.

Inside a section, `root` is an ordinary property: when the section matches,
it is recorded and printed like any other.

### Value case

The values of these six properties are lowercased when recorded:
`end_of_line`, `indent_style`, `indent_size`, `insert_final_newline`,
`trim_trailing_whitespace` and `charset`. Every other value, `tab_width` and
`max_line_length` included, is printed as written.

Lowercasing and case-insensitive comparisons only affect the ASCII letters.

## Derived indentation

After all EditorConfig files have been read, three rules run in this order.
The version is the one given with `-b` (see `cli.md`), 0.12.6 by default;
versions are compared numerically, major first, then minor, then patch.

1. From version 0.9.0 on: if `indent_style` is `tab` and `indent_size` has
   not been recorded, record `indent_size` = `tab`.
2. From version 0.9.0 on: if `indent_size` is `tab` and `tab_width` has been
   recorded, record `indent_size` = the value of `tab_width` (lowercased, as
   every `indent_size` value is).
3. If `indent_size` has been recorded and `tab_width` has not, record
   `tab_width` = the value of `indent_size`, except when the version is at
   least 0.9.0 and `indent_size` is `tab`.

These records follow the rules above, so a derived `indent_size` that replaces
an existing one keeps its position and a newly derived property comes last.
