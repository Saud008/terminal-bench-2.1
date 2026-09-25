# Family semantics

Modules sharing the same @family value are mutually exclusive in the final load plan.

When a requested module shares a family with an already-selected module:
- The previously selected module must appear in unload_sequence before the new module loads
- Family unloads precede conflict unloads when both apply

If no family is declared, the module does not participate in family swaps.
