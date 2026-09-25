# Statement split literals

Multi-statement SQL in one journal line is split on semicolons that appear outside single-quoted string literals.

A semicolon inside a string literal must not terminate a statement early.

Escaped single quotes inside literals use double single-quote syntax.
