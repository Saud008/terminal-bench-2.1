package config

import (
	"encoding/json"
	"os"
)

type Defaults struct {
	DefaultVisibilityTimeoutMs int64 `json:"default_visibility_timeout_ms"`
	DefaultHeartbeatGraceMs    int64 `json:"default_heartbeat_grace_ms"`
	ReportVersion              int   `json:"report_version"`
}

func LoadDefaults(path string) (Defaults, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return Defaults{}, err
	}
	var d Defaults
	if err := json.Unmarshal(raw, &d); err != nil {
		return Defaults{}, err
	}
	return d, nil
}
