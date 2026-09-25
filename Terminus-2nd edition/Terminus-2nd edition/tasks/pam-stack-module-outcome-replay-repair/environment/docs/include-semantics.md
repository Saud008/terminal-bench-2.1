# Include semantics

- Resolve `include` entries inline at the point they appear while flattening the stack.
- Follow nested includes recursively.
- Maximum nesting depth is **8** include frames (root stack counts as depth 1).
- A frame at depth 8 is allowed; depth 9 and beyond is an error (`depth > 8`).
- Exceeding the limit is a fatal parse error (exit code `2`).
- Relative paths resolve from `/app/fixtures/stacks/`.

Includes expand before phase execution. Module paths inside fragments are unchanged.

**Within-phase order:** when sibling includes contribute modules to the same phase, flatten preserves the include expansion order. Staging and compose must not reorder modules within a phase (for example by sorting module paths alphabetically); control-flag evaluation depends on that sequence.
