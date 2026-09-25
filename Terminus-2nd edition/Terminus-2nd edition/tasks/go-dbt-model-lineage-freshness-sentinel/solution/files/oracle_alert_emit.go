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
