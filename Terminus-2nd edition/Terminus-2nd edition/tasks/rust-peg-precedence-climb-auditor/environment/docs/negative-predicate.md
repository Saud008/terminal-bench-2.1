# Negative predicate

NegPred patterns invert inner match success at the current cursor.

Inner token literals require a full token equality match at the cursor. Prefix overlap without full token equality is not a completed inner match.

When an inner token literal partially overlaps the cursor token but does not fully match, the cursor index must remain unchanged and the neg pred must evaluate as success (inner match failed).

Advancing the cursor on partial inner overlap before neg pred completes is incorrect.
