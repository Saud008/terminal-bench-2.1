# Roam FSM states

Valid state names in fsm_states:

CONNECTED, DISCONNECTING, DISCONNECT_COMPLETE, SCANNING, ASSOCIATING, DHCP_RENEW, CONNECTED_TARGET

## Transition rules

| Step | Requirement |
|------|-------------|
| Roam start | From CONNECTED enter DISCONNECTING on roam request |
| Disconnect gate | Enter DISCONNECT_COMPLETE only after disconnect_delay_ms elapses; SCANNING is forbidden before DISCONNECT_COMPLETE |
| Scan phase | Enter SCANNING after DISCONNECT_COMPLETE; process scan.events in order |
| Associate | Enter ASSOCIATING only when scan_credited is true |
| DHCP | Enter DHCP_RENEW after service selection; gateway from target_bss |
| Complete | Append CONNECTED_TARGET when handoff_success prerequisites pass |
