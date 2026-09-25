package config

import (
	"encoding/json"
	"os"
)

type Config struct {
	ListenAddr         string `json:"listen_addr"`
	DBPath             string `json:"db_path"`
	DefaultInviteTTLMs int64  `json:"default_invite_ttl_ms"`
	MaxMembers         int    `json:"max_members"`
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
	if cfg.ListenAddr == "" {
		cfg.ListenAddr = ":8080"
	}
	if cfg.DBPath == "" {
		cfg.DBPath = "/app/work/party.db"
	}
	if cfg.DefaultInviteTTLMs == 0 {
		cfg.DefaultInviteTTLMs = 60000
	}
	if cfg.MaxMembers == 0 {
		cfg.MaxMembers = 4
	}
	return cfg, nil
}

func ClampMaxMembers(v, fallback int) int {
	if v <= 0 {
		return fallback
	}
	if v < 2 {
		return 2
	}
	if v > 8 {
		return 8
	}
	return v
}
