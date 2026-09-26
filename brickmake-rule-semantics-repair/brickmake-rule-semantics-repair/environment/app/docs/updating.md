# Updating targets

## Goals

The goals are the targets named on the command line, or the default goal.
They are updated one after the other, left to right. With no goal and no
default goal brickmake stops with `brickmake: *** No targets.  Stop.` (or
`No targets specified and no makefile found` when no makefile was read).

## Considering a file

A file is considered at most once per run. To consider a target,
brickmake:

1. runs implicit rule search if the target has no recipe (`rules.md`);
2. considers each prerequisite in order (normal and order-only; intermediate
   files as described in `rules.md`);
3. decides whether the target is out of date;
4. if it is, runs its recipe.

A file that has no rule at all and does not exist cannot be made:

```
brickmake: *** No rule to make target 'x.h', needed by 'x.o'.  Stop.
```

A target is out of date when any of these holds:

- it is phony;
- it does not exist;
- `-B` was given;
- a normal prerequisite is phony, does not exist (after it was considered),
  or has a modification time newer than the target's.

Times are compared with full (sub-second) precision.

## Time of a remade target

After a target's recipe has run, brickmake reads the target's modification
time from the file system again. A recipe that leaves its target untouched
therefore does not make the targets that depend on it out of date, and a
recipe that does not create its target leaves a missing file, which does.

A target without a recipe that was out of date (for example `FORCE:` or a
header listed with prerequisites but no recipe) is "remade" by doing
nothing; its time is simply read again. A missing file with an empty rule
thus makes everything that depends on it out of date.

With `-n`, recipes are printed instead of run, and a target whose recipe was
printed counts as newer than everything, so its dependents are printed too.
Lines prefixed with `+` run even with `-n`; a recipe made only of such lines
is treated like a normal run.

## `$?`

`$?` lists the normal prerequisites (without duplicates) that are phony,
missing, or newer than the target; all of them if the target does not
exist.

## Recipes

All lines of a recipe are expanded before the first one runs. Each line runs
in its own `/bin/sh -c`. Prefixes (`@` do not echo, `-` ignore errors, `+`
run even with `-n`) are recognized before and after expansion, and leading
blanks are removed. A line that expands to nothing is skipped. Each other
line is echoed on stdout before it runs, unless it has `@` or `-s` was
given; with `-n` every line is printed.

A failing line stops the recipe:

```
brickmake: *** [Makefile:4: all] Error 1
```

With `-`, the failure is reported and ignored:
`brickmake: [Makefile:2: all] Error 1 (ignored)`. The position is that of
the failing recipe line.

## Messages for goals

For each goal, brickmake checks whether any recipe line was run (or printed,
with `-n`) **while that goal was being updated**. If none was, it prints on
stdout:

- `brickmake: Nothing to be done for 'GOAL'.` if the goal is phony or has no
  recipe (after implicit rule search);
- `brickmake: 'GOAL' is up to date.` otherwise.

The check is made separately for every goal: `brickmake a b` where updating
`a` also made `b` prints `brickmake: 'b' is up to date.` for `b`. A goal
named twice gets the message the second time.

## Errors and `-k`

Without `-k`, the first error stops the run and brickmake exits with status
2. With `-k`, brickmake continues with the other prerequisites and goals;
targets that depend on something that failed are not remade, and for a goal
that was not remade because of a failed prerequisite it prints (on stderr,
not with `-n`):

```
brickmake: Target 'all' not remade because of errors.
```

`No rule to make target` errors end with `.  Stop.` only when brickmake
actually stops (without `-k`). The exit status is 2 if anything failed and 0
otherwise.

Intermediate files are removed at the end of the run, also after an error.
