# CEL evaluation semantics

Supported node kinds in normalized AST:

- `literal` with fields `kind` (bool, int, string, duration) and `value`
- `ident` with `name`
- `call` with `fn` (has, cel.bind) and `args` array
- `binary` with `op` (and, or, eq, lt, gt) and `left`, `right`
- `map_comp` with `key_expr`, `value_expr`, `items` (ident referencing list in env)

## has()

`has(name)` returns true when `name` exists in the evaluation environment. Each time has is invoked during evaluation it increments the run side-effect counter exposed in trace output.

## cel.bind

`cel.bind(var, value, body)` evaluates `value`, binds `var` in a new frame for `body`, then restores the previous frame. Nested binds must not restore an outer frame until the inner body completes.

## Short-circuit

`and` and `or` must not evaluate the right operand when the result is fixed by the left operand. Side effects in the right operand must not run when short-circuited.

## Duration

Duration literals use strings like `300ms`, `2s`, `1m`. Comparisons involving durations canonicalize both sides to integer nanoseconds before ordering. String forms must not be compared directly to nanosecond integers.

## Map comprehension

`map_comp` builds a map from list items. When two items produce the same key, the later item wins.
