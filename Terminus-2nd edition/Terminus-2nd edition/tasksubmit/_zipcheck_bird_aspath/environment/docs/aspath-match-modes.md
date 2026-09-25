# AS-path match modes

Each filter declares `match_mode` as one of `origin`, `transit`, or `exact`, plus `asn` and/or `as_path` as needed by that mode. Cutover evaluation uses the declared mode when deciding accept versus deny for a route's `as_path`. Mode semantics are part of the graded cutover contract in the task instruction.
