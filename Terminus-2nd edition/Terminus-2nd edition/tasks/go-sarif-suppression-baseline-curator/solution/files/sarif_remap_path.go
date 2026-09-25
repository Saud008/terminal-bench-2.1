package remap

import (
	"encoding/json"
	"os"
	"sort"
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
	out := strings.ReplaceAll(uri, "\\", "/")
	strips := append([]string(nil), cfg.PrefixStrip...)
	sort.Slice(strips, func(i, j int) bool { return len(strips[i]) > len(strips[j]) })
	for _, p := range strips {
		p = strings.ReplaceAll(p, "\\", "/")
		if strings.HasPrefix(out, p) {
			out = strings.TrimPrefix(out, p)
		}
	}
	keys := make([]string, 0, len(cfg.Rewrite))
	for k := range cfg.Rewrite {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool { return len(keys[i]) > len(keys[j]) })
	for _, k := range keys {
		if strings.HasPrefix(out, k) {
			out = cfg.Rewrite[k] + strings.TrimPrefix(out, k)
			break
		}
	}
	out = strings.TrimPrefix(out, "/")
	return out
}
