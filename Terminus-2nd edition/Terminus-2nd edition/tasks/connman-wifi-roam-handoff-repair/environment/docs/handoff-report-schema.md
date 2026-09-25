# Handoff report schema

Written by connman-roamctl simulate --export.

```json
{
  "scenario_id": "string",
  "seed": 0,
  "fsm_states": ["CONNECTED"],
  "scan_ledger": [
    {
      "event_index": 0,
      "event_type": "partial",
      "coverage": 0.0,
      "credited": false
    }
  ],
  "scan_credited": false,
  "selected_service": {
    "ssid": "string",
    "security": "string",
    "hidden": false
  },
  "dhcp_gateway": "string",
  "handoff_success": false,
  "consent_honored": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| scenario_id | string | From scenario file |
| seed | integer | CLI --seed value |
| fsm_states | array | Ordered FSM state names visited |
| scan_ledger | array | One row per scan.events entry |
| scan_credited | boolean | True when a ledger row is credited |
| selected_service | object | Ranked choice after scan credit |
| dhcp_gateway | string | Gateway installed by DHCP renew hook |
| handoff_success | boolean | True only when FSM completes CONNECTED after credited scan and valid service |
| consent_honored | boolean | False if a hidden service was selected while user_consent_hidden is false |

Rules cross-reference: /app/docs/fsm-states.md, /app/docs/scan-ledger-format.md, /app/docs/service-ranking.md, /app/docs/dhcp-renew.md.
