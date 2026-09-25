package expiryevict

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strconv"

	"github.com/terminus/pqgov/internal/model"
)

type expiryPolicy struct {
	TTLMs int64 `json:"ttl_ms"`
}

func LoadTTL(fixtureDir string, ttlBias int64) (int64, error) {
	raw, err := os.ReadFile(filepath.Join(fixtureDir, "expiry.json"))
	if err != nil {
		return 0, err
	}
	var pol expiryPolicy
	if err := json.Unmarshal(raw, &pol); err != nil {
		return 0, err
	}
	ttl := pol.TTLMs
	if bias := ttlBiasFromEnv(ttlBias); bias != 0 {
		ttl += bias
	}
	if ttl < 0 {
		ttl = 0
	}
	return ttl, nil
}

func ttlBiasFromEnv(explicit int64) int64 {
	if explicit != 0 {
		return explicit
	}
	raw := os.Getenv("TB3_TTL_BIAS")
	if raw == "" {
		return 0
	}
	v, err := strconv.ParseInt(raw, 10, 64)
	if err != nil {
		return 0
	}
	return v
}

func ShouldEvict(op model.LedgerOperation, nowMs, ttlMs int64) bool {
	age := nowMs - op.LastSeenMs
	return age > ttlMs
}

func ApplyExpiry(ops []model.LedgerOperation, nowMs, ttlMs int64) []model.LedgerOperation {
	out := make([]model.LedgerOperation, len(ops))
	copy(out, ops)
	for i := range out {
		if out[i].Status != "active" {
			continue
		}
		if ShouldEvict(out[i], nowMs, ttlMs) {
			out[i].Status = "evicted"
		}
	}
	return out
}
