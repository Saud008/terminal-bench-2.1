# Novelty check: brickmake-rule-semantics-repair

Core concept: repair a Go clone of GNU make 4.3 (`make -r -R`) so that `%` pattern
matching of directory-relative names and pattern specificity agree with the manual:
the stem length includes the directory, the directory prefix goes only to `%`
prerequisites, "ought to exist" means mentioned in the makefile, and pattern-specific
variables are applied from the shortest pattern to the longest.

## What was searched (2026-09-30)

- "terminal-bench task GNU make clone implicit rule pattern stem": no Terminal-Bench
  (TB2, TB3) or Caudal task on a make clone. Hits were only the GNU make manual and
  StackOverflow 62494658 ("GNU make not matching shortest stem"), which explains
  the ought-to-exist priority. It is a user question, not a repair task.
- "make clone Go implementation implicit rule search ought to exist pattern-specific
  variables shortest stem": GNU make `src/implicit.c` (the upstream algorithm) and the
  GNU make NEWS file. NEWS confirms two version-sensitive points we pin:
  shortest-stem ordering of pattern-specific variables arrived in 3.82, and 4.4
  narrowed "ought to exist" to prerequisites mentioned for the target itself. The
  task targets 4.3, where any mention in the makefile counts. The expected outputs
  were generated with Debian bookworm's make 4.3.
- Workspace search of every `instruction.md` for "GNU make", "pattern rule" or
  "makefile clone": this task (and its old TB 2.1 ablation job copies) are the only
  hits. There is no earlier pool task of ours on make.

## Closest public solution

- GNU make itself (`src/implicit.c`, `src/variable.c`). It is C and structured
  differently from brickmake. Porting it is not a shortcut: the agent still has to
  locate the four divergences in brickmake's own engine without breaking the rest.
- Google's kati (a make clone for Android builds, originally in Go, now in C++)
  implements implicit rules too. It is an unrelated codebase with a different data
  model, so nothing in it can be dropped into brickmake's engine.

## Differences from the TB 2.1 version of this task

The TB 2.1 bundle planted nine unrelated defects (dry-run stat, job accounting, deps
order, `+=` expansion, per-ancestor pattern sets, and more). That was a bug zoo. The
TB 4.0 redesign keeps one root cause, `%` pattern matching and specificity, with
four linked defects. The other five are fixed in the shipped code, and their tests
and rubric lines are gone.
