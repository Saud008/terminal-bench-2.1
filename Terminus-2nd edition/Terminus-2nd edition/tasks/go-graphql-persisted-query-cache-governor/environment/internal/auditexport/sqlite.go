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
	activeCount := len(snap.Operations)
	evictedCount := 0
	quotaMax := activeCount
	_, err = dst.Exec(
		`INSERT INTO pq_audit_export_meta(tenant_id, scenario, schema_hash, active_count, evicted_count, quota_max, export_revision)
		 VALUES (?, ?, ?, ?, ?, ?, ?)`,
		tenantID, scenario, snap.SchemaHash, activeCount, evictedCount, quotaMax, rev,
	)
	if err != nil {
		return err
	}
	for _, op := range snap.Operations {
		_, err := dst.Exec(
			`INSERT INTO pq_audit_operations(operation_id, tenant_id, operation_hash, schema_hash, status, registered_at_ms, last_seen_ms)
			 VALUES (?, ?, ?, ?, 'active', 0, 0)`,
			op.OperationID, tenantID, op.OperationHash, op.SchemaHash,
		)
		if err != nil {
			return err
		}
	}
	return writeSidecar(tenantID, scenario, rev)
}

func writeSidecar(tenantID, scenario string, rev int) error {
	path := "/app/output/pq-audit-meta.json"
	payload := map[string]any{
		"tenant_id":        tenantID,
		"scenario":         scenario,
		"export_revision":  rev,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
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
