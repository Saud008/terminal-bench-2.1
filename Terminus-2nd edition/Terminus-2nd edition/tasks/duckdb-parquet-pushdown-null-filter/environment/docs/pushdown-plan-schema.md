# Pushdown plan schema

Same fields as staging-plan.md. Planner selects row groups before stats pruning. Stats pruning may remove ids from selected_row_groups but must append removed ids to pruned_row_groups in filter output.

IS NULL pushdown uses null-stats-policy.md rules.
