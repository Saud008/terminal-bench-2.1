package config

import (
	"encoding/json"
	"fmt"
	"os"
)

type Config struct {
	DefaultInterestRateBps int `json:"default_interest_rate_bps"`
	MaxStackQuantity       int `json:"max_stack_quantity"`
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
	if cfg.DefaultInterestRateBps <= 0 {
		return Config{}, fmt.Errorf("default_interest_rate_bps must be positive")
	}
	if cfg.MaxStackQuantity <= 0 {
		return Config{}, fmt.Errorf("max_stack_quantity must be positive")
	}
	return cfg, nil
}
