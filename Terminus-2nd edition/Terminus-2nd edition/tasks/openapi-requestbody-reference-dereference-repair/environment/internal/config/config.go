package config

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/oasctl/internal/apperr"
)

type Config struct {
	Seed      string   `json:"seed"`
	Operation string   `json:"operation"`
	Payloads  []string `json:"payloads"`
}

func Load(path string) (Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("%w: %v", apperr.ErrIO, err)
	}
	var cfg Config
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return Config{}, fmt.Errorf("%w: %v", apperr.ErrConfig, err)
	}
	if cfg.Seed == "" || len(cfg.Payloads) == 0 {
		return Config{}, apperr.ErrConfig
	}
	return cfg, nil
}
