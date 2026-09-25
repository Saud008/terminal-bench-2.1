# Phase order

For `login`-style stacks, phases run **exactly once** in this order:

1. `auth`
2. `account`
3. `password` (only if the flattened stack lists at least one password-phase module)
4. `session`

Within each phase, modules run in flattened stack order for that phase.

If **auth** fails, do not run `account`, `password`, or `session`.

If **account** fails after auth succeeded, do not run `password` or `session`.

If **password** fails after prior phases succeeded, do not run `session`.

Empty phases are skipped.
