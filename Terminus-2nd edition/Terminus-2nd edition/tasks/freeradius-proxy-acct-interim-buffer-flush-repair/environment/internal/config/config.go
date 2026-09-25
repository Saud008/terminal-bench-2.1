package config

import (
	"encoding/json"
	"os"
)

type Config struct {
	ProxyName               string `json:"proxy_name"`
	HomeServer              string `json:"home_server"`
	DefaultInterimInterval  int    `json:"default_interim_interval_sec"`
	FlushBatchSize          int    `json:"flush_batch_size"`
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
	if cfg.DefaultInterimInterval <= 0 {
		cfg.DefaultInterimInterval = 300
	}
	if cfg.FlushBatchSize <= 0 {
		cfg.FlushBatchSize = 64
	}
	return cfg, nil
}
