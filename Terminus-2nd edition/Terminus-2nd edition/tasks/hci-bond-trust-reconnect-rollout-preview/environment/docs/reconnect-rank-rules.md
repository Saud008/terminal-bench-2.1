# Reconnect rank contract

Eligible devices (those blocked by none of the gates) are ranked deterministically across the entire fleet, not per adapter: sort by `criticality` ascending, then by `mac` ascending (lexicographic). Each eligible row in the ledger and atlas carries `adapter_id`, `mac`, `salted_id`, `criticality`, `gatt_service_count`, `reconnect_attempts`, and its 1-indexed `rank` in that sorted order.

When a single device would be blocked by more than one gate at once, exactly one `reason` is recorded, using this precedence, highest first: `ineligible_pairing_required`, then `ineligible_resume_armed`, then `ineligible_power_sequence`, then `ineligible_reconnect_storm`. For example a device with an armed resume slot that is also over the reconnect-storm budget is recorded as `ineligible_resume_armed`, not `ineligible_reconnect_storm`.

Re-running `compile` against the same scanned fleet must produce the same eligible rank and the same reasons every time; ranking must not depend on adapter iteration order or device iteration order in the underlying fleet inventory.
