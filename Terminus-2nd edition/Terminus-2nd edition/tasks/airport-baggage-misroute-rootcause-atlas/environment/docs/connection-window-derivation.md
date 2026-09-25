# connection-window-derivation.md

Minimum connection feasibility compares inbound flight arr_minute to outbound flight dep_minute.

gap_minutes = outbound.dep_minute - inbound.arr_minute

Feasible when gap_minutes >= min_connect_minutes from the hub connection row matching inbound and outbound flight ids.

TB3_MCT_MINUTES replaces min_connect_minutes for verifier-only hub reruns.

Boundary-equal gaps (gap equals minimum) must classify as feasible.
