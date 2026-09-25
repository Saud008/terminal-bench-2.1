#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

cat > /app/internal/enabledpolicy/refs.go <<'ORACLE_ENABLED'
package enabledpolicy

import (
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func EnabledReferencesDisabled(models []model.ModelNode) bool {
	enabled := map[string]bool{}
	disabled := map[string]bool{}
	for _, m := range models {
		if m.Enabled {
			enabled[m.UniqueID] = true
		} else {
			disabled[m.UniqueID] = true
		}
	}
	for _, m := range models {
		if !m.Enabled {
			continue
		}
		for _, dep := range m.DependsOn {
			if disabled[dep] {
				return false
			}
			if len(dep) >= 6 && dep[:6] == "model." && !enabled[dep] {
				return false
			}
		}
	}
	return true
}
ORACLE_ENABLED

cat > /app/internal/packstate/snapshot.go <<'ORACLE_PACKSTATE'
package packstate

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/packload"
)

func WriteSnapshot(path, seed, bundle string, raw model.ManifestBundle) error {
	prev := int64(0)
	if b, err := os.ReadFile(path); err == nil {
		var old model.StagingSnapshot
		if json.Unmarshal(b, &old) == nil {
			prev = old.IngestSeq
		}
	}
	mat := packload.Materialize(raw, seed)
	snap := model.StagingSnapshot{
		IngestSeq:   prev + 1,
		Seed:        seed,
		Pack:        bundle,
		GeneratedAt: raw.GeneratedAt,
		EvaluatedAt: raw.EvaluatedAt,
		Models:      mat.Models,
		Sources:     mat.Sources,
		Exposures:   mat.Exposures,
	}
	return writeJSON(path, snap)
}

func ReadSnapshot(path string) (model.StagingSnapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.StagingSnapshot{}, err
	}
	var snap model.StagingSnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.StagingSnapshot{}, err
	}
	return snap, nil
}

func ValidateSeedBundle(snap model.StagingSnapshot, seed, bundle string) error {
	if snap.Seed != seed || snap.Pack != bundle {
		return fmt.Errorf("staging seed/bundle mismatch")
	}
	return nil
}

func writeJSON(path string, v any) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}
ORACLE_PACKSTATE

cat > /app/internal/graphorder/traverse.go <<'ORACLE_TOPO'
package graphorder

import (
	"sort"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func EnabledTopo(models []model.ModelNode) []string {
	byID := map[string]model.ModelNode{}
	enabled := map[string]bool{}
	for _, m := range models {
		byID[m.UniqueID] = m
		if m.Enabled {
			enabled[m.UniqueID] = true
		}
	}
	visited := map[string]bool{}
	out := []string{}
	var visit func(string)
	visit = func(id string) {
		if visited[id] || !enabled[id] {
			return
		}
		visited[id] = true
		m := byID[id]
		for _, d := range m.DependsOn {
			if enabled[d] {
				visit(d)
			}
		}
		out = append(out, id)
	}
	ids := make([]string, 0, len(enabled))
	for id := range enabled {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	for _, id := range ids {
		visit(id)
	}
	return out
}
ORACLE_TOPO

cat > /app/internal/sourcewindow/evaluate.go <<'ORACLE_FRESH'
package sourcewindow

import (
	"os"
	"strconv"
	"time"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func ParseRFC3339(s string) (time.Time, error) {
	return time.Parse(time.RFC3339, s)
}

func biasMinutes() int {
	v := os.Getenv("TB3_FRESHNESS_BIAS_MINUTES")
	if v == "" {
		return 0
	}
	n, _ := strconv.Atoi(v)
	return n
}

func EvaluateSources(sources []model.SourceNode, evaluatedAt string) ([]model.FreshnessStatus, error) {
	eval, err := ParseRFC3339(evaluatedAt)
	if err != nil {
		return nil, err
	}
	out := make([]model.FreshnessStatus, 0, len(sources))
	for _, s := range sources {
		loaded, err := ParseRFC3339(s.LoadedAt)
		if err != nil {
			return nil, err
		}
		mins := int(eval.Sub(loaded).Minutes()) + biasMinutes()
		status := "ok"
		if mins > s.WarnAfterMinutes {
			status = "warn"
		}
		if mins > s.ErrorAfterMinutes {
			status = "error"
		}
		out = append(out, model.FreshnessStatus{
			UniqueID: s.UniqueID,
			Minutes:  mins,
			Status:   status,
		})
	}
	return out, nil
}
ORACLE_FRESH

cat > /app/internal/downstream/closure.go <<'ORACLE_EXPOSURE'
package downstream

import (
	"sort"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func Closure(exposures []model.ExposureNode, models []model.ModelNode) map[string][]string {
	modelSet := map[string]model.ModelNode{}
	for _, m := range models {
		modelSet[m.UniqueID] = m
	}
	var collect func(string, map[string]bool)
	collect = func(id string, seen map[string]bool) {
		if seen[id] {
			return
		}
		m, ok := modelSet[id]
		if !ok {
			return
		}
		seen[id] = true
		for _, d := range m.DependsOn {
			collect(d, seen)
		}
	}
	out := map[string][]string{}
	for _, e := range exposures {
		seen := map[string]bool{}
		for _, d := range e.DependsOn {
			collect(d, seen)
		}
		refs := make([]string, 0, len(seen))
		for id := range seen {
			refs = append(refs, id)
		}
		sort.Strings(refs)
		out[e.UniqueID] = refs
	}
	return out
}
ORACLE_EXPOSURE

cat > /app/internal/scanstore/sqlite.go <<'ORACLE_SCAN'
package scanstore

import (
	"database/sql"
	"encoding/json"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"

	_ "modernc.org/sqlite"
)

type DB struct {
	conn *sql.DB
}

func Open(path string) (*DB, error) {
	conn, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	if _, err := conn.Exec(`CREATE TABLE IF NOT EXISTS scans (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		seed TEXT NOT NULL,
		pack TEXT NOT NULL,
		summary_json TEXT NOT NULL,
		active INTEGER NOT NULL DEFAULT 1
	)`); err != nil {
		conn.Close()
		return nil, err
	}
	return &DB{conn: conn}, nil
}

func (d *DB) Close() error {
	return d.conn.Close()
}

func InsertScan(d *DB, seed, bundle string, summary model.ScanSummary) (int64, error) {
	if _, err := d.conn.Exec(`UPDATE scans SET active=0 WHERE seed=?`, seed); err != nil {
		return 0, err
	}
	body, err := json.Marshal(summary)
	if err != nil {
		return 0, err
	}
	res, err := d.conn.Exec(
		`INSERT INTO scans (seed, pack, summary_json, active) VALUES (?, ?, ?, 1)`,
		seed, bundle, string(body),
	)
	if err != nil {
		return 0, err
	}
	return res.LastInsertId()
}

func LatestScan(d *DB, seed, bundle string) (int64, model.ScanSummary, error) {
	row := d.conn.QueryRow(
		`SELECT id, summary_json FROM scans WHERE seed=? AND pack=? AND active=1 ORDER BY id DESC LIMIT 1`,
		seed, bundle,
	)
	var id int64
	var body string
	if err := row.Scan(&id, &body); err != nil {
		return 0, model.ScanSummary{}, err
	}
	var summary model.ScanSummary
	if err := json.Unmarshal([]byte(body), &summary); err != nil {
		return 0, model.ScanSummary{}, err
	}
	return id, summary, nil
}
ORACLE_SCAN

cat > /app/internal/emittalerts/alerts.go <<'ORACLE_ALERT'
package emittalerts

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/packstate"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/enabledpolicy"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/runscan"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/scanstore"
)

var severityRank = map[string]int{"error": 0, "warn": 1, "ok": 2}

func BuildReport(stagingPath, dbPath, seed, bundle string) (model.AlertReport, error) {
	snap, err := packstate.ReadSnapshot(stagingPath)
	if err != nil {
		return model.AlertReport{}, err
	}
	if err := packstate.ValidateSeedBundle(snap, seed, bundle); err != nil {
		return model.AlertReport{}, err
	}
	res, err := runscan.ComputeFromSnapshot(snap)
	if err != nil {
		return model.AlertReport{}, err
	}
	db, err := scanstore.Open(dbPath)
	if err != nil {
		return model.AlertReport{}, err
	}
	defer db.Close()
	scanID, summary, err := scanstore.LatestScan(db, seed, bundle)
	if err != nil {
		return model.AlertReport{}, err
	}
	alerts := buildAlerts(res.Freshness, res.ExposureRefs, snap.Models)
	rep := model.AlertReport{
		Seed:         seed,
		Pack:         bundle,
		ScanID:       scanID,
		ModelOrder:   res.ModelOrder,
		Freshness:    res.Freshness,
		ExposureRefs: res.ExposureRefs,
		Alerts:       alerts,
		Summary:      summary,
	}
	rep.AuditDigest = auditDigest(rep)
	return rep, nil
}

func buildAlerts(fresh []model.FreshnessStatus, refs map[string][]string, models []model.ModelNode) []model.AlertRow {
	rows := []model.AlertRow{}
	for _, f := range fresh {
		if f.Status == "ok" {
			continue
		}
		rows = append(rows, model.AlertRow{
			AlertCode: "SOURCE_STALE",
			Severity:  f.Status,
			SubjectID: f.UniqueID,
			Message:   fmt.Sprintf("source stale %d min", f.Minutes),
		})
	}
	disabledSet := map[string]bool{}
	for _, m := range models {
		if !m.Enabled {
			disabledSet[m.UniqueID] = true
		}
	}
	for _, m := range models {
		if !m.Enabled {
			continue
		}
		for _, dep := range m.DependsOn {
			if disabledSet[dep] {
				rows = append(rows, model.AlertRow{
					AlertCode: "DISABLED_UPSTREAM",
					Severity:  "error",
					SubjectID: m.UniqueID,
					Message:   fmt.Sprintf("depends on disabled %s", dep),
				})
			}
		}
	}
	for exp, modelRefs := range refs {
		if len(modelRefs) == 0 {
			rows = append(rows, model.AlertRow{
				AlertCode: "EXPOSURE_EMPTY",
				Severity:  "warn",
				SubjectID: exp,
				Message:   "exposure has no model refs",
			})
		}
	}
	_ = enabledpolicy.EnabledReferencesDisabled(models)
	sort.Slice(rows, func(i, j int) bool {
		a, b := rows[i], rows[j]
		if severityRank[a.Severity] != severityRank[b.Severity] {
			return severityRank[a.Severity] < severityRank[b.Severity]
		}
		if a.AlertCode != b.AlertCode {
			return a.AlertCode < b.AlertCode
		}
		return a.SubjectID < b.SubjectID
	})
	return rows
}

func auditDigest(rep model.AlertReport) string {
	body := auditBody(rep)
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}

type alertDigestRow struct {
	AlertCode string `json:"alert_code"`
	Message   string `json:"message"`
	Severity  string `json:"severity"`
	SubjectID string `json:"subject_id"`
}

func auditBody(rep model.AlertReport) string {
	alertRows := make([]alertDigestRow, len(rep.Alerts))
	for i, row := range rep.Alerts {
		alertRows[i] = alertDigestRow{
			AlertCode: row.AlertCode,
			Message:   row.Message,
			Severity:  row.Severity,
			SubjectID: row.SubjectID,
		}
	}
	alertsJSON, _ := json.Marshal(alertRows)
	refsJSON, _ := json.Marshal(rep.ExposureRefs)
	orderJSON, _ := json.Marshal(rep.ModelOrder)
	summaryJSON, _ := json.Marshal(map[string]any{
		"disabled_ref_ok":     rep.Summary.DisabledRefOK,
		"enabled_model_count": rep.Summary.EnabledModelCount,
		"exposure_count":      rep.Summary.ExposureCount,
		"stale_source_count":  rep.Summary.StaleSourceCount,
	})
	return fmt.Sprintf(
		`{"alerts":%s,"exposure_refs":%s,"model_order":%s,"summary":%s}`,
		string(alertsJSON),
		string(refsJSON),
		string(orderJSON),
		string(summaryJSON),
	)
}

func WriteReport(path string, rep model.AlertReport) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}
ORACLE_ALERT


cd /app
go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/dbtsent ./cmd/dbtsent
bash /app/scripts/reset-state.sh
test -x /usr/local/bin/dbtsent
