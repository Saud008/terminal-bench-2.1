# Recursive reference guard

Ref collection follows $ref edges depth-first. Before resolving an in-document JSON pointer target, the walker records the pair (schema_id, json_pointer_to_ref) in a visit stack.

If the same pair is encountered again while still on the stack, the edge status must be recursive instead of resolved. Leaving a subschema pops the pair.

Guarding only the schema_id without the pointer causes false recursive hits on unrelated refs inside the same file and is incorrect.
