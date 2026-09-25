# Migration journal format

Each line is one JSON object with fields seq, version, direction, and sql.

The seq field orders journal replay. direction is up or down. version is the golang-migrate version integer for that step.

SQL may contain multiple statements separated by semicolons outside single-quoted string literals.
