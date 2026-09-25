package config

import (
	"encoding/json"
	"fmt"
	"os"
)

type TableConfig struct {
	VersionColumn string `json:"version_column"`
	PrimaryKey    string `json:"primary_key"`
	TTLColumn     string `json:"ttl_column"`
	TTLGraceMS    int64  `json:"ttl_grace_ms"`
}

func Load(path string) (TableConfig, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return TableConfig{}, err
	}
	var cfg TableConfig
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return TableConfig{}, err
	}
	if cfg.VersionColumn == "" || cfg.PrimaryKey == "" {
		return TableConfig{}, fmt.Errorf("invalid table config")
	}
	return cfg, nil
}

func TableSuffix() string {
	if v := os.Getenv("CHPARTS_TABLE_SUFFIX"); v != "" {
		return v
	}
	return "default"
}

func TableName() string {
	return fmt.Sprintf("TB3_%s_events", TableSuffix())
}
