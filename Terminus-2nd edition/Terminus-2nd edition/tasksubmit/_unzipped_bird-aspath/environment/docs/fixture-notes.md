# Fixture notes

Public scenarios under /app/fixtures/peers/: basic-wave, inherit-override, transit-match, wave-tie, critical-abort, rewrite-wellknown, exact-path.

The critical-abort inventory uses peer_id `early` for the first-wave peer (wave_rank 1) and peer_id `late` for the aborting peer (wave_rank 2, abort_on_critical_deny true). After a critical deny abort, rib_after for peer_id early must match the salted checkpoint (pre-mutation communities and med).

Hidden verifier scenarios may be under /opt/verifier-fixtures/bgpcut/.
