package config

import (
	"encoding/json"
	"os"
)

type Config struct {
	SchemaVersion       int      `json:"schema_version"`
	RollupIntervalSec   int      `json:"rollup_interval_sec"`
	CacheTTLSec         int      `json:"cache_ttl_sec"`
	StalenessWindowSec  int      `json:"staleness_window_sec"`
	GraceWindowSec      int      `json:"grace_window_sec"`
	DownsampleTiers     []string `json:"downsample_tiers"`
	RetentionStartUTC   string   `json:"retention_start_utc"`
	RetentionEndUTC     string   `json:"retention_end_utc"`
}

func Load(path string) (Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return Config{}, err
	}
	var cfg Config
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return Config{}, err
	}
	if cfg.SchemaVersion == 0 {
		cfg.SchemaVersion = 1
	}
	return cfg, nil
}

func (c Config) IntervalMs() int64 {
	return int64(c.RollupIntervalSec) * 1000
}
