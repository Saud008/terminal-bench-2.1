# Restore planner JSON

Schema: pg-wal-restore-plan/1

| Field | Meaning |
|-------|---------|
| restore_ready | true when continuity_ok, selected_segment set, no blocking partials |
| restore_target_time | Normalized UTC from --restore-target |
| target_timeline | Timeline id of selected segment |
| selected_segment | WAL filename chosen for restore target |
| continuity_ok | No segment gaps on any timeline in staging |
| gaps | Array of {timeline, from_segment, to_segment} |
| partial_rejected | Partial files blocking restore through selected segment |
| digest | Copied from staging snapshot |

Exit codes: plan exits 0 when restore_ready true, 2 when false, 1 on missing staging.

JSON keys sorted with indent 2 and trailing newline.
