# Critical deny abort

Inventories list `critical_prefixes`. Peers may set `abort_on_critical_deny`. When a critical deny aborts the wave, the ledger and sealed report must show `wave_aborted` and the deny row with `aborted=true`. RIB post-state rules for an aborted wave are stated in the task instruction.
