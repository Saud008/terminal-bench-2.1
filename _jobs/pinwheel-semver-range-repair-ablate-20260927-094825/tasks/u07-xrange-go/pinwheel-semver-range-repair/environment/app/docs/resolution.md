# Resolution

`pinwheel resolve` turns a project's `pin.json` into a `pin.lock`. The lock
is flat: a package appears at most once, at a single version.

## Terms

- The **selection** maps package names to one release each. It starts empty.
- A package is **required** when it can be reached from the project's
  `dependencies` by following the dependencies of selected releases. A
  package that is reached but has no selected release yet is required, but
  its own dependencies are not followed until it has one.
- The **dependents** of a required package are the project (written
  `<root>`) if it lists the package, plus every required package whose
  selected release lists it.
- The **constraints** on a required package are the ranges its dependents
  wrote for it.

## Overrides

If the project's `overrides` names a package, the override range is the only
constraint on that package: the ranges its dependents wrote are ignored,
although they are still its dependents. An override never makes a package
required on its own.

## Choosing a release

A release of a package is **eligible** when it satisfies every constraint on
the package and is not yanked. A yanked release is eligible anyway if one of
the constraints is an exact pin that it satisfies. An exact pin is a range
that is a single full version, bare or with `=` (`1.4.2`, `=1.4.2`,
`2.0.0-beta.3`), and nothing else: no wildcards, other operators or `||`.

Among the eligible releases pinwheel picks the one with the highest
precedence, or the lowest when the project sets `"prefer": "lowest"`. When
the best candidates have equal precedence (they differ only in build
metadata), the one with the latest `published` time wins, whichever way
`prefer` points; if those are equal too, the one listed later in the registry
file wins.

## Rounds

Resolution runs in rounds. Each round:

1. works out the required packages and their constraints from the selection
   left by the previous round,
2. chooses a release for every required package, each independently of the
   others,
3. replaces the selection with exactly those choices. Packages that are no
   longer required drop out of the selection.

Resolution is finished when a round produces the same selection it started
from; that selection is what gets locked, together with the dependents of
each package as computed in that round. If it hasn't finished after 100
rounds, resolution fails.

## Failures

Resolution fails, with exit status 3, when:

- a required package is not in the registry:
  `pinwheel: unknown package "NAME" (required by DEPENDENTS)`
- a required package has no eligible release:
  `pinwheel: no version of NAME satisfies CONSTRAINTS`, where each constraint
  is shown as `"RANGE" (from DEPENDENT)` and an override as
  `"RANGE" (from <overrides>)`
- the selection does not settle within 100 rounds.

Resolution stops at the first round that hits a failure.
