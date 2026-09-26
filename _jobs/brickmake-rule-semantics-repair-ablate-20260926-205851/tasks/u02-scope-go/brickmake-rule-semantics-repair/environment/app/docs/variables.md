# Variables

## References

`$(NAME)`, `${NAME}` and `$X` (one character) refer to variables; `$$` is a
literal `$`. A reference whose name contains references is expanded first:
`$($(KIND)_SRCS)`. `$(NAME:from=to)` is a substitution reference: without
`%` it replaces the suffix `from` of each word by `to`; with `%` it works
like `$(patsubst from,to,$(NAME))`. Undefined variables expand to nothing.

## Flavors

A **recursive** variable (`=`) stores its text unexpanded; every reference
expands it again, so it sees the current values of the variables it uses. A
recursive variable that refers to itself is an error:
`Makefile:1: *** Recursive variable 'A' references itself (eventually).  Stop.`

A **simple** variable (`:=` or `::=`) is expanded once, when it is assigned,
and stores the result.

`$(flavor NAME)` reports `recursive`, `simple` or `undefined`.

## Appending

`NAME += text` on a variable that is not defined is the same as
`NAME = text`.

On an existing variable, `+=` keeps the variable's flavor:

- recursive: the unexpanded `text` is added to the unexpanded value, so it
  is expanded with the rest of the value at every reference;
- simple: `text` is expanded **now** and the result is added to the stored
  value. The variable stays simple.

The two parts are separated by one space. If the added part is empty (after
expansion, for a simple variable) the value is unchanged; if the old value
is empty the result is just the added part.

```
BASE := -Wall
BASE += $(EXTRA)   # EXTRA is not defined yet: BASE stays "-Wall", simple
EXTRA = -Werror
```

## Conditional assignment

`NAME ?= text` does nothing if `NAME` is defined at all, even with an empty
value. Otherwise it is `NAME = text`.

## Command-line and environment variables

`NAME=value` arguments define recursive variables, `NAME:=value` simple
ones. A command-line variable cannot be changed by the makefile: ordinary
assignments to it are ignored, and every target-specific or
pattern-specific definition of the same name takes the command-line value.

Environment variables are imported as recursive variables with origin
`environment` (except `SHELL`, which is always `/bin/sh`). A makefile
assignment replaces them. Recipes run with the process environment plus the
command-line variables.

## Target-specific variables

```
release: CFLAGS = -O3
test:    CFLAGS += -DTEST
debug:   OPT := $(BASE) -g
lib.a:   AR ?= ar
```

A target-specific definition applies while that target's recipe is expanded
and while its prerequisites are considered, recursively: a prerequisite that
is first reached through `release` sees `release`'s definitions (unless it
has its own). A file is considered once, so the context of the first target
that asks for it is the one it keeps.

The operators behave as follows for target-specific (and pattern-specific)
definitions:

- `=` and `:=` define the variable for the target; `:=` expands the value
  when the line is read.
- `?=` defines the variable for the target only if no variable of that name
  is visible when the line is read (the target's earlier definitions and
  the global variables defined so far). For a pattern-specific `?=` the
  check is made when the file's pattern set is built, against the earlier
  definitions in that set and the global variables as they are at the end
  of reading.
- `+=` extends the target's own earlier definition if the same target
  already defined the variable (`test: CFLAGS = -O0` then
  `test: CFLAGS += -DTEST` gives `-O0 -DTEST`), following the rules of
  "Appending" above. Otherwise it appends to whatever value is visible from
  the enclosing context **when the variable is used**: the global value, the
  inherited value from the parent target, and so on. In that case the added
  text is always expanded at use (even if the enclosing variable is simple),
  and the separating space is added whenever the enclosing value is not
  empty.

## Pattern-specific variables

```
build/%.o: CFLAGS += -fPIC
%.o:       OPT = generic
```

A definition whose target contains `%` applies to every file whose whole
name matches the pattern (`a%.o` matches `ab.o` but not `lib/ab.o`).

All pattern-specific definitions that match a file are combined into one
set for that file. They are applied from the shortest pattern to the
longest, and patterns of equal length in makefile order, using the
target-specific rules above; later definitions replace or extend earlier
ones. The most specific pattern therefore wins, regardless of the order in
the makefile:

```
CFLAGS = -O2
build/net/%.o: CFLAGS += -DNET
build/%.o:     CFLAGS += -fPIC
# build/net/sock.o gets "-O2 -fPIC -DNET"
```

## Lookup order

When a variable is used for a file, brickmake searches:

1. the file's own target-specific variables,
2. the file's pattern-specific set,
3. the variables of the target that first asked for the file (its own
   target-specific variables, then its pattern-specific set, then its own
   parent, and so on),
4. the global variables.

A file's own pattern-specific variables therefore take precedence over
anything inherited from its parent. A `+=` definition found at one level is
appended to the value found by continuing the search at the next level.

```
V = g
parent: V += p
%.o: V += pat
c.o: V += own
parent: c.o
# c.o, reached through parent, sees "g p pat own"
```

## Automatic variables

| Variable | Value |
|---|---|
| `$@` | the target |
| `$<` | the first prerequisite |
| `$^` | the normal prerequisites, duplicates removed |
| `$+` | the normal prerequisites, in order, with duplicates |
| `$\|` | the order-only prerequisites, duplicates removed |
| `$?` | the normal prerequisites newer than the target (see `updating.md`) |
| `$*` | the stem of an implicit or static pattern rule match; empty otherwise |

`$(@D)`, `$(@F)` and the other `D`/`F` variants give the directory (without
the trailing slash, `.` if none) and the file part of each word.
`$(origin @)` is `automatic` inside recipes.

## Other variables

`SHELL` (`/bin/sh`), `CURDIR`, `MAKECMDGOALS` and `.DEFAULT_GOAL` are
defined. `$(origin NAME)` reports `undefined`, `default`, `environment`,
`file`, `command line` or `automatic`.
