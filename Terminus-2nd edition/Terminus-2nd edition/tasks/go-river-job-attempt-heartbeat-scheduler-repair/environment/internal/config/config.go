package config

import (
	"encoding/json"
	"os"
)

type Config struct {
	Listen       string `json:"listen"`
	DBPath       string `json:"db_path"`
	LeaseMs      int64  `json:"lease_ms"`
	BackoffBase  int64  `json:"backoff_base_ms"`
	DefaultMax   int    `json:"max_poison_attempts_default"`
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
	if cfg.LeaseMs <= 0 {
		cfg.LeaseMs = 30_000
	}
	if cfg.BackoffBase <= 0 {
		cfg.BackoffBase = 1_000
	}
	if cfg.DefaultMax <= 0 {
		cfg.DefaultMax = 5
	}
	return cfg, nil
}
