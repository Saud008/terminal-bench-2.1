package config

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/collectdctl/internal/model"
)

func Load(path string) (model.Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Config{}, err
	}
	var cfg model.Config
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return model.Config{}, err
	}
	if cfg.FlushIntervalSec <= 0 {
		return model.Config{}, fmt.Errorf("invalid flush interval")
	}
	if cfg.TimeSkewSec < 0 {
		return model.Config{}, fmt.Errorf("invalid skew")
	}
	return cfg, nil
}

func SelectBatches(seed string, batches []string) []string {
	if len(batches) == 0 {
		return nil
	}
	sum := sha256.Sum256([]byte(seed))
	bits := uint16(sum[0]) | uint16(sum[1])<<8
	limit := len(batches)
	if limit > 16 {
		limit = 16
	}
	selected := make([]string, 0, limit)
	for i := 0; i < limit; i++ {
		if (bits>>uint(i))&1 == 1 {
			selected = append(selected, batches[i])
		}
	}
	if len(selected) == 0 {
		selected = append(selected, batches[int(sum[2])%len(batches)])
	}
	out := append([]string(nil), selected...)
	digest := sum[:]
	for i := len(out) - 1; i > 0; i-- {
		j := int(digest[i%len(digest)]) % (i + 1)
		out[i], out[j] = out[j], out[i]
	}
	return out
}
