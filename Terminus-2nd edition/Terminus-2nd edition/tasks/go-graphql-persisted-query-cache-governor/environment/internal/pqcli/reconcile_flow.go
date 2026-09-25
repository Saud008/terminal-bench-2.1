package pqcli

import (
	"os"
	"strconv"

	"github.com/terminus/pqgov/internal/ledgerreconcile"
)

func ReconcileTenant(tenantID, scenario, fixtureDir string) error {
	nowMs := ledgerreconcile.NowMs()
	if raw := os.Getenv("PQGOV_NOW_MS"); raw != "" {
		if v, err := strconv.ParseInt(raw, 10, 64); err == nil {
			nowMs = v
		}
	}
	_, err := ledgerreconcile.RunReconcile(tenantID, scenario, fixtureDir, nowMs, 0, 0)
	return err
}
