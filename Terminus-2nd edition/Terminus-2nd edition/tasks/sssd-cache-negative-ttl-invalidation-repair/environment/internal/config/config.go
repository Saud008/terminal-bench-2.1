package config

import (
	"encoding/json"
	"os"
)

type Config struct {
	NegativeTTLSec       int    `json:"negative_ttl_sec"`
	DomainSuffix         string `json:"domain_suffix"`
	NestedInvalidation   bool   `json:"nested_invalidation"`
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
	if cfg.NegativeTTLSec <= 0 {
		cfg.NegativeTTLSec = 15
	}
	if cfg.DomainSuffix == "" {
		cfg.DomainSuffix = "example"
	}
	if override := os.Getenv("SSSD_DOMAIN_SUFFIX"); override != "" {
		cfg.DomainSuffix = override
	}
	return cfg, nil
}
