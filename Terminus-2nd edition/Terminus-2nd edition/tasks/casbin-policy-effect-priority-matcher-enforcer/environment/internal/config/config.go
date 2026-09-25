package config

import (
	"encoding/json"
	"fmt"
	"os"
)

type Config struct {
	Model   string   `json:"model"`
	Seed    string   `json:"seed"`
	Bundles []string `json:"bundles"`
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
	if cfg.Model == "" {
		return Config{}, fmt.Errorf("model required")
	}
	if cfg.Seed == "" {
		cfg.Seed = "default"
	}
	if len(cfg.Bundles) == 0 {
		return Config{}, fmt.Errorf("bundles required")
	}
	return cfg, nil
}
