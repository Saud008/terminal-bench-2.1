# tmpfiles-replay product spec

tmpfiles-replay is an offline simulator for a subset of systemd tmpfiles.d behavior. Scenarios ship a synthetic filesystem tree (tree.json) and a rule list (rules.conf) or generator fragments (fragments/*.conf). Apply mutates the tree in memory and exports surviving paths plus an action trace.

Rule line shapes:

- d PATH MODE USER GROUP AGE — ensure directory exists (apply is a no-op when path already present unless recreate/z applies).
- r! GLOB AGE [eN] — remove paths matching GLOB when age gate passes; optional eN sets exclude depth (see /app/docs/exclude-glob.md).
- x GLOB — exclude marker consumed by the nearest prior r! line in the same pass.
- z PATH MODE USER GROUP — recreate path (directory when MODE starts with 0, else file) after age cleanup on the same subtree completes (see /app/docs/recreate-order.md).
- o PATH MODE USER GROUP — ownership change that must be recorded before any remove deletes PATH (see /app/docs/ownership-order.md).

Generator fragments are named boot.*.conf or boot-ex.*.conf. boot mode merges only boot fragments; boot-ex mode merges boot plus boot-ex fragments (see /app/docs/generator-boot.md).

Age tokens accept plain seconds or suffix forms s, m, h, d. Export JSON schema is in /app/docs/export-schema.md.
