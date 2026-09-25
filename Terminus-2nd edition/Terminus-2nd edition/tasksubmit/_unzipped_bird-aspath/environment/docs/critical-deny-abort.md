# Critical deny abort

Deep-copy the salted RIB before evaluation. If a deny hits a prefix listed in critical_prefixes and peer.abort_on_critical_deny is true: include that deny row with aborted=true, set wave_aborted=true, restore rib_after from the checkpoint (discard earlier mutations), and stop.
