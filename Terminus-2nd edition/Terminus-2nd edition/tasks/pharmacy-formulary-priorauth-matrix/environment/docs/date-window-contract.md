# Date window tie-break

A rule is active when as_of is greater than or equal to effective_start and less than or equal to effective_end when end is non-empty.

When multiple rules tie on priority, the rule with the latest effective_start on or before as_of wins.
