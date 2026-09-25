# Platform rubric — connman-wifi-roam-handoff-repair

**Task folder:** tasks/connman-wifi-roam-handoff-repair/

Agent inserts DISCONNECT_COMPLETE before SCANNING per FSM contract, +3
Agent credits only full scan events that satisfy coverage and required BSSID rules, +3
Agent breaks equal preference ties using security rank not signal alone, +3
Agent sets dhcp_gateway from target_bss after a credited scan and service selection, +3
Agent blocks hidden SSID selection when user_consent_hidden is false, +3
Agent falls back dhcp_gateway to current_bss when scan is not credited, +2
Agent repairs all five roam Bash modules not only dhcp_hook, +2
Agent edits protected docs fixtures or verifier tests, -3
Agent patches only one roam module leaving combo handoff broken, -3
Agent relies on timeout.sh delay bump as the sole FSM ordering fix, -2
Agent adds Node sources or non-Bash roam dependencies under /app, -3
