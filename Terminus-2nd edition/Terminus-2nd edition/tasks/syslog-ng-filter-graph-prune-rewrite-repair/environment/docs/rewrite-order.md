# Rewrite template order

Facility gate filters run before rewrite templates. A message that fails every pure-facility gate in filters.conf is dropped and never rewritten.

Pure-facility gates are filters whose expression is exactly facility(name) with no other atoms.

After the facility gate passes, apply each rewrite whose filter_ref matches the current message. A rewrite template is prefixed to the program field (template + program).

Rewrites must not run before the facility gate stage completes.
