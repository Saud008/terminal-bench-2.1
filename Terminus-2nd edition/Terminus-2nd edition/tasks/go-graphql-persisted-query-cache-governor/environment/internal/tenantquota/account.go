package tenantquota

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strconv"

	"github.com/terminus/pqgov/internal/model"
)

type quotaCatalog struct {
	Tenants map[string]quotaRow `json:"tenants"`
}

type quotaRow struct {
	MaxActive int `json:"max_active"`
}

func LoadMaxActive(tenantID, fixtureDir string, quotaBias int) (int, error) {
	raw, err := os.ReadFile(filepath.Join(fixtureDir, "quotas.json"))
	if err != nil {
		return 0, err
	}
	var cat quotaCatalog
	if err := json.Unmarshal(raw, &cat); err != nil {
		return 0, err
	}
	row, ok := cat.Tenants[tenantID]
	if !ok {
		return 0, nil
	}
	maxActive := row.MaxActive
	if bias := quotaBiasFromEnv(quotaBias); bias != 0 {
		maxActive += bias
	}
	if maxActive < 0 {
		maxActive = 0
	}
	return maxActive, nil
}

func quotaBiasFromEnv(explicit int) int {
	if explicit != 0 {
		return explicit
	}
	raw := os.Getenv("TB3_QUOTA_BIAS")
	if raw == "" {
		return 0
	}
	v, err := strconv.Atoi(raw)
	if err != nil {
		return 0
	}
	return v
}

func CountTowardQuota(ops []model.LedgerOperation) int {
	return len(ops)
}

func Headroom(maxActive, activeCount int) int {
	if maxActive <= activeCount {
		return 0
	}
	return maxActive - activeCount
}
