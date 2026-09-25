package config

import (
	"encoding/json"
	"fmt"
	"os"
)

// Config is loaded from /app/config/relationwatch.json.
type Config struct {
	ListenAddr             string `json:"listen_addr"`
	DBPath                 string `json:"db_path"`
	SnapshotPath           string `json:"snapshot_path"`
	ExportPath             string `json:"export_path"`
	WatchStaleLagThreshold int64  `json:"watch_stale_lag_threshold"`
	ClosureCacheSize       int    `json:"closure_cache_size"`
	FixtureDir             string `json:"fixture_dir"`
}

// Load reads JSON config from path.
func Load(path string) (*Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config: %w", err)
	}
	var cfg Config
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return nil, fmt.Errorf("parse config: %w", err)
	}
	if cfg.ListenAddr == "" {
		cfg.ListenAddr = ":8787"
	}
	if cfg.DBPath == "" {
		cfg.DBPath = "/app/data/relationwatch.db"
	}
	if cfg.SnapshotPath == "" {
		cfg.SnapshotPath = "/app/state/revision-snapshot.json"
	}
	if cfg.ExportPath == "" {
		cfg.ExportPath = "/app/output/authz-report.json"
	}
	if cfg.WatchStaleLagThreshold == 0 {
		cfg.WatchStaleLagThreshold = 2
	}
	if cfg.ClosureCacheSize == 0 {
		cfg.ClosureCacheSize = 256
	}
	if cfg.FixtureDir == "" {
		cfg.FixtureDir = "/app/fixtures"
	}
	return &cfg, nil
}
