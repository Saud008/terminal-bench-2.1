package config

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
)

type Config struct {
	Listen          string `json:"listen"`
	DBPath          string `json:"db_path"`
	GraceMs         int64  `json:"grace_ms"`
	SkewToleranceMs int64  `json:"skew_tolerance_ms"`
	VaultHMACKey    string `json:"vault_hmac_key"`
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
	if cfg.Listen == "" {
		cfg.Listen = ":8080"
	}
	if cfg.DBPath == "" {
		cfg.DBPath = "/app/work/livattest.db"
	}
	if cfg.GraceMs <= 0 {
		cfg.GraceMs = 5000
	}
	if cfg.SkewToleranceMs <= 0 {
		cfg.SkewToleranceMs = 2000
	}
	return cfg, nil
}

func (c Config) Validate() error {
	if c.Listen == "" {
		return fmt.Errorf("listen required")
	}
	if c.VaultHMACKey == "" {
		return fmt.Errorf("vault_hmac_key required")
	}
	if _, err := hex.DecodeString(c.VaultHMACKey); err != nil {
		return fmt.Errorf("vault_hmac_key: %w", err)
	}
	return nil
}

func (c Config) VaultKeyBytes() ([]byte, error) {
	return hex.DecodeString(c.VaultHMACKey)
}
