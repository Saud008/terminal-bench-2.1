# Window fit contract

Each fleet inventory declares `window_hours`, the number of hours available in the scheduled maintenance window. Each array declares `estimated_hours`, the operator's estimate of how long that array's reshape will run.

An array is blocked with reason `blocked_window` only when `estimated_hours` is strictly greater than `window_hours`.

An array whose `estimated_hours` equals `window_hours` fits exactly inside the window and is not blocked by this gate. Only a strict overrun blocks the array.
