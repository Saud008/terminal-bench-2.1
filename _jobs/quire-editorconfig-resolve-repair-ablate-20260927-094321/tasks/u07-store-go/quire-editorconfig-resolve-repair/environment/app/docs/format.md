# EditorConfig file format

An EditorConfig file is read line by line. A UTF-8 byte order mark at the very
start of the file is ignored. Whitespace below means space, tab, line feed,
vertical tab, form feed and carriage return, so CRLF line endings behave like
LF. Leading and trailing whitespace of every line is ignored.

After that trimming, a line is one of:

- empty;
- a comment: its first character is `;` or `#`;
- a section header: its first character is `[`;
- a property: anything else, which must contain `=` or `:`.

## Inline comments

A `;` or `#` later in a line starts a comment only when the character right
before it is whitespace. The comment runs to the end of the line.

| Line | Result |
|---|---|
| `color = #ff0000` | value `#ff0000` |
| `list = a;b` | value `a;b` |
| `list = a ;b` | value `a` |
| `[*.txt] ; text files` | section `*.txt` |
| `[*.txt;x]` | section `*.txt;x` |

The value of a property is examined on its own after the whitespace following
the separator has been skipped: a `;` or `#` at the start of the value is not
preceded by whitespace within the value and is kept (`a = ;x` has value `;x`).

## Section headers

The section name is the text between the `[` and the last `]` that comes
before an inline comment; whatever follows that `]` is ignored. The name is
used verbatim, spaces included. A header line without such a `]` is a syntax
error. A header whose name is longer than 4096 bytes is ignored: the line is
skipped and the previous section continues.

Properties before the first section header make up the preamble. They belong
to the section named "" whose glob never matches a file, so the only
meaningful preamble property is `root` (see `resolution.md`).

## Properties

The separator is the first `=` on the line. Only when there is no `=` before
an inline comment is the first `:` used instead. So `d: x=y` sets `d: x` to
`y`, and `c = x:y` sets `c` to `x:y`. A line whose separator would only come
after an inline comment has no separator and is a syntax error.

The name is the text before the separator with trailing whitespace removed.
The value is the text after it with leading whitespace removed, then the
inline comment removed, then trailing whitespace removed. Empty values are
allowed. A property whose name is longer than 1024 bytes or whose value is
longer than 4096 bytes is ignored.

## Syntax errors

A header line without a closing `]` and a property line without a separator
are syntax errors. Reading continues after an error, but the file is reported
with the number of its first error line (lines count from 1, comment and
blank lines included) and resolution stops (see `cli.md`).
