# Scenario bundle layout

Each scenario is a JSON file under /app/fixtures/scenarios/.

```json
{
  "scenario_id": "string",
  "current_bss": {
    "ssid": "string",
    "bssid": "string",
    "gateway": "string"
  },
  "target_bss": {
    "ssid": "string",
    "bssid": "string",
    "gateway": "string"
  },
  "disconnect_delay_ms": 0,
  "scan": {
    "required_bssids": ["string"],
    "events": [
      {
        "type": "partial",
        "bssids_seen": ["string"],
        "coverage": 0.0
      }
    ]
  },
  "services": [
    {
      "ssid": "string",
      "security": "wpa3",
      "signal": -50,
      "hidden": false,
      "preference": 0
    }
  ],
  "hidden_candidate": {
    "ssid": "string",
    "security": "wpa2",
    "signal": -40,
    "hidden": true,
    "preference": 0
  },
  "user_consent_hidden": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| scenario_id | string | Stable scenario name |
| current_bss | object | Active association before roam |
| target_bss | object | Intended roam target |
| disconnect_delay_ms | integer | Simulated disconnect completion delay |
| scan.required_bssids | array | BSSIDs that must be seen on a credited scan |
| scan.events | array | Ordered scan passes (partial or full) |
| services | array | Visible service candidates |
| hidden_candidate | object or null | Optional hidden SSID candidate |
| user_consent_hidden | boolean | Whether hidden auto-connect is allowed |

Security tokens: wpa3, wpa2, wpa, open.
