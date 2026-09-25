// Package cipcfg loads the slsacip runtime configuration JSON.
package cipcfg

import (
	"encoding/json"
	"fmt"
	"os"
)

// Config mirrors /app/config/slsacip.json.
type Config struct {
	Seed          string   `json:"seed"`
	QuorumK       int      `json:"quorum_k"`
	TrustRootsDir string   `json:"trust_roots_dir"`
	PoliciesRoot  string   `json:"policies_root"`
	PolicyPacks   []string `json:"policy_packs"`
	EnvelopesDir  string   `json:"envelopes_dir"`
}

// Load reads and parses the config JSON at path.
func Load(path string) (Config, error) {
	var cfg Config
	b, err := os.ReadFile(path)
	if err != nil {
		return cfg, fmt.Errorf("read config %s: %w", path, err)
	}
	if err := json.Unmarshal(b, &cfg); err != nil {
		return cfg, fmt.Errorf("parse config %s: %w", path, err)
	}
	return cfg, nil
}
