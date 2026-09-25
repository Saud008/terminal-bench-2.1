# Apply export schema

Apply export JSON fields:

- scenario: string scenario name
- seed: opaque seed string from CLI
- now: integer epoch seconds used for the pass
- surviving_paths: sorted list of path strings still present in the tree
- actions: ordered list of objects with type remove, recreate, or ownership

remove actions include path. recreate actions include path. ownership actions include path, user, group.

Generate export JSON fields:

- scenario, mode (boot or boot-ex)
- rule_lines: array of merged rule strings
- line_count: integer length of rule_lines
