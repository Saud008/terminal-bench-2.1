# Platform rubric — bash-mdadm-reshape-bitmap-hold-preview

**Task folder:** tasks/bash-mdadm-reshape-bitmap-hold-preview/
**Written:** 2026-07-16T12:39:12Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements mdreshape scan compile publish on the Bash mdadm reshape baseline, +3
Agent applies host_salt to produce salted_name for each array during scan, +3
Agent advances load_seq by one when inventory already exists for the run-id, +2
Agent blocks arrays with internal or external bitmap unless bitmap_clear_planned is true, +3
Agent blocks arrays when any spare device appears in fleet spare_holds, +3
Agent enforces degraded floors raid1=1 raid5=3 raid6=4 raid10=2 on active_disks, +3
Agent rejects illegal level transitions including raid6 to raid5 and any raid0 path, +3
Agent blocks reshape when estimated_hours is strictly greater than window_hours, +2
Agent orders eligible arrays by criticality ascending then name ascending, +3
Agent seals audit_digest with mdreshape|v1| canonical payload including blocked name:reason pairs, +2
Agent leaves device_slot_sorter decoy off the scan compile publish hot path, +1
Agent only clears external bitmap freezes while internal bitmaps remain ignored, -3
Agent checks only spares[0] against spare_holds and misses later held spares, -3
Agent treats estimated_hours equal to window_hours as a blocked_window failure, -3
Agent sorts eligible rows by name only ignoring criticality, -3
Agent recomputes gate outcomes inside publish instead of reading reshape-ledger, -2
