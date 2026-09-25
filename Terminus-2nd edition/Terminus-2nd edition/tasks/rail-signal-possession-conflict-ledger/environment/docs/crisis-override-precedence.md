# Crisis override precedence

Crisis overrides carry priority 0. During the override half-open window on its blocks, any possession or reservation with priority greater than zero is suppressed from conflict detection when the claim blocks intersect the override blocks protected zone.

Suppressed claims must not appear in conflict_groups. The summary field override_suppressed counts how many possession and reservation claims were suppressed across all priority-0 overrides.

Overrides with non-zero priority behave like ordinary claims.
