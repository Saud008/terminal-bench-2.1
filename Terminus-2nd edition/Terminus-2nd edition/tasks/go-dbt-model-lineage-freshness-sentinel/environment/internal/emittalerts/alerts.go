package emittalerts

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/packstate"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/runscan"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/scanstore"
)

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
	_ = models
	return rows
}

func auditDigest(rep model.AlertReport) string {
	body := fmt.Sprintf("%s:%s:%d", rep.Seed, rep.Pack, rep.ScanID)
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
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
