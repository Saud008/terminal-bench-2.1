# Rules

## Explicit rules

```
app: main.o util.o
	cc -o $@ $^
```

A target may appear in several rules. Only one of them may have a recipe (a
later recipe replaces an earlier one with a warning on stderr). The
prerequisites of all its rules are combined in this order: those of the
implicit rule (if one is used, see below), then those of the rule that has
the recipe, then those of the other rules in makefile order.

```
x: p1
x: p2 p3
	@echo $^      # p2 p3 p1 p4
x: p4
```

`a b: c` is the same as two rules `a: c` and `b: c`.

## Order-only prerequisites

Prerequisites after a `|` word are order-only: they are brought up to date
before the target, but their timestamps never make the target out of date,
and they appear only in `$|`. A name that is also a normal prerequisite of
the same target (in any of its rules) is a normal prerequisite only; it is
dropped from the order-only list.

## Static pattern rules

```
OBJS := obj/x.o obj/y.o
$(OBJS): obj/%.o: src/%.c | obj
	cc -c $< -o $@
```

Each target is matched against the target pattern as a whole (no directory
handling) and `%` in each prerequisite is replaced by the stem, which is
also `$*`. A target that does not match gets a warning and no
prerequisites from the rule.

## Pattern rules

```
%.o: %.c
	cc -c $< -o $@
%.tab.c %.tab.h: %.y
	bison -d $<
```

A rule whose targets all contain `%` is a pattern rule. A rule with several
target patterns makes all of its targets with one run of its recipe.

Defining a pattern rule with the same targets and prerequisites as an
existing one replaces it, and the new rule counts as defined at the new
position. The same definition without a recipe cancels the existing rule.
Pattern rules are never the default goal. A rule whose only target is `%`
(match-anything) is not supported and is ignored.

## Implicit rule search

A file that is not phony and has no recipe from an explicit or static
pattern rule is looked up among the pattern rules, even if it exists.

**Matching.** A target pattern that contains a slash is matched against the
whole file name. A target pattern without a slash is matched against the
file part of a name that has a directory; the directory is then put in
front of the stem. For `src/eat` and the rule `e%t: c%r`, the stem is
`src/a` and the prerequisite is `src/car`. In such a directory-relative
match the directory is added only to prerequisites that contain `%`:
with `%.o: %.c config.h`, `net/sock.o` depends on `net/sock.c` and
`config.h`.

The stem must not be empty.

**Choosing.** All matching rules are ordered by the length of their stem,
directory part included, shortest first; rules with equally long stems keep
their makefile order. For `lib/a.o`, the rule `lib/%.o: lib/%.c` (stem `a`)
comes before `%.o: %.c` (stem `lib/a`), wherever each is defined.

The rules are then tried in that order, in two passes:

1. A rule applies if each of its prerequisites (normal and order-only)
   exists as a file or **ought to exist**: it is mentioned in the makefile
   as a target or as a prerequisite of an explicit rule, or it was entered
   by an earlier implicit rule search. A mentioned prerequisite does not need
   a rule of its own; if it has none and does not exist, the build then fails
   with `No rule to make target`.
2. If no rule applies, the rules are tried again, and a prerequisite that
   neither exists nor ought to exist is also accepted if it can itself be
   made by implicit rule search (a chain). A rule is not used twice in one
   chain.

The first rule that applies is used: its recipe, its stem as `$*`, and its
prerequisites, which come before the target's explicit prerequisites.

## Intermediate files

A file that was accepted only through a chain in the second pass is
**intermediate**. Intermediate files are treated specially:

- A missing intermediate file does not by itself make its dependent out of
  date. The dependent is out of date only if the intermediate file exists
  and is newer, or if something the intermediate file depends on (checked
  recursively through further intermediates) is newer than the dependent.
- An intermediate file is made only when its dependent has to be remade,
  after the dependent's other prerequisites have been considered.
- Intermediate files made during the run are deleted at the end, printing
  `rm FILE ...` (one line for all of them) unless `-s` was given. With `-n`
  the line is printed but nothing is deleted.

Files listed as prerequisites of `.SECONDARY` or `.PRECIOUS` are never
deleted; `.SECONDARY` without prerequisites keeps all of them. Files that
exist or are mentioned in the makefile are never intermediate.

## Secondary expansion

After `.SECONDEXPANSION:` appears, the prerequisite lists of the rules that
follow are expanded a second time when their target is considered. `$$`
survives the first expansion as `$`, so `$$@` and `$$*` refer to the target
and the stem, and `$$($$@_OBJS)` to a per-target variable. The second
expansion uses the target's variables. For static pattern rules and pattern
rules, `%` in the result is then replaced by the stem as usual.

## Special targets

| Target | Effect |
|---|---|
| `.PHONY` | prerequisites are phony: always remade, never looked up among pattern rules |
| `.SECONDEXPANSION` | enables secondary expansion for the rules that follow |
| `.SECONDARY`, `.PRECIOUS` | intermediate files that are kept |
| `.SUFFIXES`, `.DEFAULT`, `.INTERMEDIATE`, `.NOTINTERMEDIATE`, `.DELETE_ON_ERROR`, `.IGNORE`, `.SILENT`, `.NOTPARALLEL`, `.ONESHELL`, `.POSIX`, `.EXPORT_ALL_VARIABLES`, `.LOW_RESOLUTION_TIME` | accepted and ignored |

## Default goal

The default goal is the first target of the first explicit or static
pattern rule that does not start with `.` (a target containing `/` is
allowed even if it starts with `.`). Assigning `.DEFAULT_GOAL` overrides
it; the value at the end of reading is used.
