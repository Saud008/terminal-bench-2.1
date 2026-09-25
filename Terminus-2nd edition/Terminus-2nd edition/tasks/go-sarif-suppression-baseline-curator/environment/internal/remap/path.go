package remap

import (
	"encoding/json"
	"os"
	"strings"

	"github.com/terminus/sarbctl-curator/internal/model"
)

func Load(path string) (model.RemapConfig, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.RemapConfig{}, err
	}
	var cfg model.RemapConfig
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return model.RemapConfig{}, err
	}
	return cfg, nil
}

func Apply(uri string, cfg model.RemapConfig) string {
	out := uri
	if len(cfg.PrefixStrip) > 0 {
		p := cfg.PrefixStrip[0]
		if strings.HasPrefix(out, p) {
			out = strings.TrimPrefix(out, p)
		}
	}
	return out
}
