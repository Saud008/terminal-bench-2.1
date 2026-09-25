# Rule match semantics

## Rule ordering

Rules are collected from every file in RULES_DIR (sorted by basename). Within a file, non-comment lines keep file order.

Each rule receives:

- rule_id: basename:line (1-based line number in file)
- priority: integer from OPTIONS+=priority=N when present, else 1000 plus file index times 100 plus line number
- source_file: basename only
- line_number: 1-based

Effective order is ascending sort by tuple (priority, source_file, line_number). Later rules in this order override earlier rules for symlink collisions and permission fields.

## Token matching

Rules are comma-separated KEY==value tokens (udev subset).

- SUBSYSTEM, KERNEL, ATTR{name}, MODALIAS use double-quoted values.
- KERNEL and MODALIAS patterns support shell globs where * matches any substring.
- ATTR matching uses the device attribute map after inheritance.

## Attribute inheritance

Devices may include parent_id. Walk parent_id links to the root. Child attrs override parent attrs. Matching uses the merged map.

## Modalias catalog

MODALIAS_TSV is tab-separated alias pattern and canonical tag per line. A device modalias matches a rule MODALIAS token when either equals the device modalias or the catalog maps the device modalias to a tag that glob-matches the rule token.

## Match edges

For each device, record every rule that matches after inheritance and modalias resolution. Store rule_id list in match order (ascending effective order).
