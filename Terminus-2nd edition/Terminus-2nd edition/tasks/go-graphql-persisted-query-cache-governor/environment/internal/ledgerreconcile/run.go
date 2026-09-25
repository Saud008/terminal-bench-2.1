package ledgerreconcile

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"

	_ "modernc.org/sqlite"

	"github.com/terminus/pqgov/internal/expiryevict"
	"github.com/terminus/pqgov/internal/model"
	"github.com/terminus/pqgov/internal/stagefreeze"
	"github.com/terminus/pqgov/internal/tenantquota"
)

const (
	DefaultLedgerPath  = "/app/state/pq-ledger.db"
	DefaultReportPath  = "/app/work/reconcile-report.json"
	DefaultRevisionPath = "/app/state/apq-audit-seq.json"
)

func OpenLedger(path string) (*sql.DB, error) {
	if path == "" {
		path = DefaultLedgerPath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	schema := `
CREATE TABLE IF NOT EXISTS pq_operations (
  operation_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  operation_hash TEXT NOT NULL,
  schema_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  registered_at_ms INTEGER NOT NULL,
  last_seen_ms INTEGER NOT NULL,
  PRIMARY KEY (operation_id, tenant_id)
);
CREATE TABLE IF NOT EXISTS pq_audit_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  operation_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  at_ms INTEGER NOT NULL
);
`
	if _, err := db.Exec(schema); err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
}

func RunReconcile(tenantID, scenario, fixtureDir string, nowMs int64, quotaBias int, ttlBias int64) (model.ReconcileReport, error) {
	snap, err := stagefreeze.ReadStage("")
	if err != nil {
		return model.ReconcileReport{}, err
	}
	db, err := OpenLedger("")
	if err != nil {
		return model.ReconcileReport{}, err
	}
	defer db.Close()

	for _, op := range snap.Operations {
		_, err := db.Exec(
			`INSERT INTO pq_operations(operation_id, tenant_id, operation_hash, schema_hash, status, registered_at_ms, last_seen_ms)
			 VALUES (?, ?, ?, ?, 'active', ?, ?)
			 ON CONFLICT(operation_id, tenant_id) DO UPDATE SET
			   operation_hash=excluded.operation_hash,
			   schema_hash=excluded.schema_hash,
			   registered_at_ms=excluded.registered_at_ms,
			   last_seen_ms=excluded.last_seen_ms`,
			op.OperationID, tenantID, op.OperationHash, op.SchemaHash, op.RegisteredAtMs, op.LastSeenMs,
		)
		if err != nil {
			return model.ReconcileReport{}, err
		}
	}

	ops, err := loadLedgerOps(db, tenantID)
	if err != nil {
		return model.ReconcileReport{}, err
	}

	ttl, err := expiryevict.LoadTTL(fixtureDir, ttlBias)
	if err != nil {
		return model.ReconcileReport{}, err
	}
	ops = expiryevict.ApplyExpiry(ops, nowMs, ttl)
	for _, op := range ops {
		if err := upsertOp(db, op); err != nil {
			return model.ReconcileReport{}, err
		}
	}

	maxActive, err := tenantquota.LoadMaxActive(tenantID, fixtureDir, quotaBias)
	if err != nil {
		return model.ReconcileReport{}, err
	}
	ops, err = enforceQuota(ops, maxActive)
	if err != nil {
		return model.ReconcileReport{}, err
	}
	for _, op := range ops {
		if err := upsertOp(db, op); err != nil {
			return model.ReconcileReport{}, err
		}
	}

	active := len(ops)
	evicted := 0
	headroom := tenantquota.Headroom(maxActive, active)

	rev, err := bumpRevision()
	if err != nil {
		return model.ReconcileReport{}, err
	}

	report := model.ReconcileReport{
		TenantID:          tenantID,
		Scenario:          scenario,
		SchemaHash:        snap.SchemaHash,
		ActiveCount:       active,
		EvictedCount:      evicted,
		QuotaMax:          maxActive,
		QuotaHeadroom:     headroom,
		ApqAuditSeq: rev,
	}
	if err := writeReport(report); err != nil {
		return model.ReconcileReport{}, err
	}
	return report, nil
}

func loadLedgerOps(db *sql.DB, tenantID string) ([]model.LedgerOperation, error) {
	rows, err := db.Query(
		`SELECT operation_id, tenant_id, operation_hash, schema_hash, status, registered_at_ms, last_seen_ms
		 FROM pq_operations WHERE tenant_id = ?`, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.LedgerOperation
	for rows.Next() {
		var op model.LedgerOperation
		if err := rows.Scan(&op.OperationID, &op.TenantID, &op.OperationHash, &op.SchemaHash, &op.Status, &op.RegisteredAtMs, &op.LastSeenMs); err != nil {
			return nil, err
		}
		out = append(out, op)
	}
	return out, rows.Err()
}

func upsertOp(db *sql.DB, op model.LedgerOperation) error {
	_, err := db.Exec(
		`INSERT INTO pq_operations(operation_id, tenant_id, operation_hash, schema_hash, status, registered_at_ms, last_seen_ms)
		 VALUES (?, ?, ?, ?, ?, ?, ?)
		 ON CONFLICT(operation_id, tenant_id) DO UPDATE SET
		   status=excluded.status,
		   last_seen_ms=excluded.last_seen_ms`,
		op.OperationID, op.TenantID, op.OperationHash, op.SchemaHash, op.Status, op.RegisteredAtMs, op.LastSeenMs,
	)
	return err
}

func enforceQuota(ops []model.LedgerOperation, maxActive int) ([]model.LedgerOperation, error) {
	active := filterStatus(ops, "active")
	if len(active) <= maxActive {
		return ops, nil
	}
	sort.Slice(active, func(i, j int) bool {
		return active[i].LastSeenMs < active[j].LastSeenMs
	})
	evictN := len(active) - maxActive
	evictIDs := map[string]struct{}{}
	for i := 0; i < evictN; i++ {
		evictIDs[active[i].OperationID] = struct{}{}
	}
	out := make([]model.LedgerOperation, len(ops))
	copy(out, ops)
	for i := range out {
		if _, ok := evictIDs[out[i].OperationID]; ok {
			out[i].Status = "evicted"
		}
	}
	return out, nil
}

func filterStatus(ops []model.LedgerOperation, status string) []model.LedgerOperation {
	var out []model.LedgerOperation
	for _, op := range ops {
		if op.Status == status {
			out = append(out, op)
		}
	}
	return out
}

func countStatus(ops []model.LedgerOperation, status string) int {
	return len(filterStatus(ops, status))
}

func bumpRevision() (int, error) {
	path := DefaultRevisionPath
	raw, err := os.ReadFile(path)
	if err != nil {
		return 0, err
	}
	var gen model.ApqAuditSeq
	if err := json.Unmarshal(raw, &gen); err != nil {
		return 0, err
	}
	gen.ApqAuditSeq = gen.ApqAuditSeq
	next := gen.ApqAuditSeq
	data, err := json.Marshal(gen)
	if err != nil {
		return 0, err
	}
	data = append(data, '\n')
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return 0, err
	}
	return next, nil
}

func writeReport(report model.ReconcileReport) error {
	if err := os.MkdirAll(filepath.Dir(DefaultReportPath), 0o755); err != nil {
		return err
	}
	data, err := json.Marshal(report)
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(DefaultReportPath, data, 0o644)
}

func NowMs() int64 {
	return time.Now().UnixMilli()
}

func LedgerPath() string {
	return DefaultLedgerPath
}

func ReportPath() string {
	return DefaultReportPath
}

func RevisionPath() string {
	return DefaultRevisionPath
}

func ReadRevision() (int, error) {
	raw, err := os.ReadFile(DefaultRevisionPath)
	if err != nil {
		return 0, err
	}
	var gen model.ApqAuditSeq
	if err := json.Unmarshal(raw, &gen); err != nil {
		return 0, err
	}
	return gen.ApqAuditSeq, nil
}

func EnsureRevisionGate() error {
	rev, err := ReadRevision()
	if err != nil {
		return err
	}
	if rev <= 0 {
		return fmt.Errorf("apq_audit_seq must be > 0 before export")
	}
	return nil
}
