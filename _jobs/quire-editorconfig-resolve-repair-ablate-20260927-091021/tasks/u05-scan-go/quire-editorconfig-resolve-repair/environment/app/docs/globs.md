# Section globs

A property applies to a file when the glob built from its section header
matches the file's full path. The glob must match the whole path.

## From header to glob

`DIR` is the directory that holds the EditorConfig file, i.e. its path up to
the last `/` (the empty string for `/.editorconfig`).

| Header | Glob |
|---|---|
| contains no `/` | `DIR` + `**/` + header |
| starts with `/` | `DIR` + header |
| contains `/`, but not first | `DIR` + `/` + header |

So `[*.sh]` applies to shell scripts at any depth below `DIR`, while
`[scripts/*.sh]` applies only to `DIR/scripts/*.sh`, exactly like
`[/scripts/*.sh]`.

`DIR` is inserted escaped: each of the characters `?` `[` `]` `\` `*` `-` `{`
`}` `,` in it is preceded by a backslash, so a directory such as
`/srv/work/[wip] shop` or `/srv/alt{1,2}` matches only itself.

## Wildcards

| Glob | Matches |
|---|---|
| `*` | any run of characters other than `/`, including none |
| `**` | any run of characters, `/` included |
| `?` | one character other than `/` |
| `/**/` | a single `/`, or `/` + any path + `/` (zero or more directories) |
| `[abc]`, `[a-z]` | one character from the set |
| `[!abc]` | one character not in the set |
| `{a,b,c}` | any one of the alternatives |
| `{N1..N2}` | an integer from N1 to N2, see below |
| `\c` | the character `c` itself |

Every other character matches itself, including `,` outside braces, `-`
outside brackets and `^`. Matching is case-sensitive.

## Brackets

Inside a bracket expression, `-` between two characters is a range and `!`
right after the `[` negates the set. `^` is an ordinary character: `[^a]`
matches `^` or `a`.

When a `/` occurs between the `[` and the next `]`, the bracket is not a
character class: the text from `[` through that `]` matches itself, so
`[a/b]` only matches the five characters `[a/b]`. A `[` that is never closed
makes the whole glob match nothing.

## Braces

Braces only take effect when every `}` closes an earlier `{` and there are as
many of each (escaped braces do not count); otherwise every brace in the glob
is an ordinary character.

A brace group with a comma at its top level is a list of alternatives, which
may themselves contain wildcards and brace groups; an alternative may be
empty. A group without such a comma is special:

- `{}` and `{word}` match the text itself, braces included;
- `{N1..N2}`, where N1 and N2 are integers with an optional `+` or `-`,
  matches an optionally signed integer whose value lies between N1 and N2
  inclusive. A number written with a leading `0`, `0` itself included, never
  matches, and when N1 is greater than N2 nothing matches.

How ranges are checked has one catch. Every `{N1..N2}` and every `/**/` in
the glob is a numbered group, counted from the left. The first range is
checked against the text of the first numbered group, the second range
against the second group, and so on, whether or not that group is the range
itself. The text matched by a `/**/` starts with `/` and counts as the value
0 (it has no leading `0`). So `v{1..9}/**/*.md` matches `v3/a.md` and
`v3/x/a.md`, while `docs/**/v{1..9}/*.md` matches nothing, because its range
is checked against the `/**/` group; and `a/**/b{-1..1}` matches `a/b5`.
