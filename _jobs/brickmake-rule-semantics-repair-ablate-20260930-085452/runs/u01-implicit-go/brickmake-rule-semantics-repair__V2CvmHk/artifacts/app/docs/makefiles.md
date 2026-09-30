# Reading makefiles

## Which file

Without `-f`, brickmake reads the first of `GNUmakefile`, `makefile` and
`Makefile` that exists. `-f FILE` may be given several times; the files are
read in order. Positions in messages use the file name as given.

## Lines

A backslash at the end of a line joins it with the next one. Outside
recipes, the backslash, the newline, trailing blanks before the backslash
and leading blanks of the next line become a single space. In recipe lines
the backslash-newline is kept and passed to the shell; one leading tab of
the continuation line is removed.

`#` starts a comment outside recipe lines. `\#` is a literal `#`. Comments
are not stripped from recipe lines, which go to the shell as written.

Whitespace before a comment is part of the line, so `DIR = out # build dir`
assigns `out ` (with a trailing space) to `DIR`.

## Recipe lines

A line that starts with a tab and follows a rule line (possibly separated by
blank lines, comment lines and conditional directives) is a recipe line of
that rule. A rule may also carry its first recipe line after a `;` on the
rule line: `all: ; @echo done`. Any other line ends the recipe.

A tab-prefixed line that does not follow a rule is read as an ordinary line.

## Conditionals

```
ifeq (A,B)    ifeq "A" "B"    ifeq 'A' "B"
ifneq ...     ifdef NAME      ifndef NAME
else          else ifeq ...   endif
```

Conditionals nest and may appear anywhere, including between recipe lines.
Both arguments of `ifeq`/`ifneq` are expanded before they are compared. In
the parenthesized form the first argument keeps its leading blanks but loses
its trailing blanks, and the second argument loses its leading blanks but
keeps its trailing blanks: `ifeq ( a , a )` compares ` a` with `a ` and is
false.

`ifdef NAME` expands `NAME` to get a variable name and is true when that
variable is defined with a non-empty value. The value itself is not
expanded: after `E =` and `R = $(E)`, `ifdef R` is true and `ifdef E` is
false. A simple variable assigned an empty expansion (`S := $(E)`) is
empty, so `ifdef S` is false.

## Assignments

```
NAME = value      recursive
NAME := value     simple (also ::=)
NAME += value     append
NAME ?= value     set only if NAME is not defined
```

The line is an assignment when an assignment operator appears before any
other `:` (outside variable references). Leading blanks of the value are
removed; trailing blanks are kept. The name is expanded.
See `variables.md` for the meaning of each operator.

A line that is neither an assignment nor a rule is expanded; if the result
is empty (for example a line holding only `$(info ...)`) it is ignored,
otherwise it is an error: `Makefile:3: *** missing separator.  Stop.`

## Rule lines

```
targets : prerequisites [| order-only prerequisites] [; recipe]
targets : target-pattern : prerequisite-patterns [| order-only ...] [; recipe]
targets : NAME op value
```

Targets and prerequisites are expanded when the line is read (see
`rules.md` for secondary expansion). A rule line whose remainder after the
first `:` is an assignment defines target-specific or pattern-specific
variables; such a value may contain `;`.

Double-colon rules are not supported.

## Unsupported directives

`define`, `endef`, `include`, `-include`, `sinclude`, `override`, `export`,
`unexport`, `vpath`, `undefine`, `private` and `load` stop brickmake with
`*** unsupported directive 'NAME'.  Stop.`
