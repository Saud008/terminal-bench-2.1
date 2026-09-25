# Dependency resolution build contract

whres implements build-and-dependency-management style resolution over offline package indexes. Constraint specifiers act like lockfile pins. The resolution snapshot fingerprint supports reproducible rebuild of candidate reports across cargo rebuild cycles.

Supply chain reviewers use emit output to audit which wheel rows satisfy dependency pins under a fixed marker environment.
