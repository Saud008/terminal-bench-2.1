package auditexport

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"

	"github.com/terminus/pqgov/internal/ledgerreconcile"
	"github.com/terminus/pqgov/internal/stagefreeze"
)

const DefaultAuditPath = "/app/output/pq-audit.sqlite"

func ExportAudit(tenantID, scenario, output string) error {
	if output == "" {
		output = DefaultAuditPath
	}
	if err := ledgerreconcile.EnsureRevisionGate(); err != nil {
		return err
	}
	snap, err := stagefreeze.ReadStage("")
	if err != nil {
		return err
	}
	rev, err := ledgerreconcile.ReadRevision()
	if err != nil {
		return err
	}
	reportRaw, err := os.ReadFile(ledgerreconcile.ReportPath())
	if err != nil {
		return err
	}
	var report struct {
		QuotaMax     int `json:"quota_max"`
		ActiveCount  int `json:"active_count"`
		EvictedCount int `json:"evicted_count"`
	}
	if err := json.Unmarshal(reportRaw, &report); err != nil {
		return err
	}
	src, err := sql.Open("sqlite", ledgerreconcile.LedgerPath())
	if err != nil {
		return err
	}
	defer src.Close()
	if err := os.MkdirAll(filepath.Dir(output), 0o755); err != nil {
		return err
	}
	_ = os.Remove(output)
	dst, err := sql.Open("sqlite", output)
	if err != nil {
		return err
	}
	defer dst.Close()
	schema := `
CREATE TABLE pq_audit_export_meta (
  tenant_id TEXT NOT NULL,
  scenario TEXT NOT NULL,
  schema_hash TEXT NOT NULL,
  active_count INTEGER NOT NULL,
  evicted_count INTEGER NOT NULL,
  quota_max INTEGER NOT NULL,
  export_revision INTEGER NOT NULL
);
CREATE TABLE pq_audit_operations (
  operation_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  operation_hash TEXT NOT NULL,
  schema_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  registered_at_ms INTEGER NOT NULL,
  last_seen_ms INTEGER NOT NULL
);
`
	if _, err := dst.Exec(schema); err != nil {
		return err
	}
	_, err = dst.Exec(
		`INSERT INTO pq_audit_export_meta(tenant_id, scenario, schema_hash, active_count, evicted_count, quota_max, export_revision)
		 VALUES (?, ?, ?, ?, ?, ?, ?)`,
		tenantID, scenario, snap.SchemaHash, report.ActiveCount, report.EvictedCount, report.QuotaMax, rev,
	)
	if err != nil {
		return err
	}
	rows, err := src.Query(
		`SELECT operation_id, tenant_id, operation_hash, schema_hash, status, registered_at_ms, last_seen_ms
		 FROM pq_operations WHERE tenant_id = ? ORDER BY operation_id`,
		tenantID,
	)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var opID, tid, ohash, shash, status string
		var reg, seen int64
		if err := rows.Scan(&opID, &tid, &ohash, &shash, &status, &reg, &seen); err != nil {
			return err
		}
		_, err := dst.Exec(
			`INSERT INTO pq_audit_operations(operation_id, tenant_id, operation_hash, schema_hash, status, registered_at_ms, last_seen_ms)
			 VALUES (?, ?, ?, ?, ?, ?, ?)`,
			opID, tid, ohash, shash, status, reg, seen,
		)
		if err != nil {
			return err
		}
	}
	return rows.Err()
}

func AuditPath() string {
	return DefaultAuditPath
}

func ValidateExportMeta(dbPath string) error {
	if _, err := os.Stat(dbPath); err != nil {
		return fmt.Errorf("missing audit export: %w", err)
	}
	return nil
}
