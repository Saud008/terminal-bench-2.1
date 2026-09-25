package sealpublish

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/bbreleasectl/internal/model"
	"github.com/terminus/bbreleasectl/internal/emergaudit"
	"github.com/terminus/bbreleasectl/internal/persist"
)

func PublishLedger(scenario string, outPath string) error {
	db, err := persist.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	pass := readPass()
	if pass <= 0 {
		return fmt.Errorf("screening_pass must be positive")
	}
	sid, err := persist.GetMeta(db, "scenario_id")
	if err != nil {
		return err
	}
	releases, err := buildReleases(db)
	if err != nil {
		return err
	}
	for _, rel := range releases {
		_, _ = db.Exec(`INSERT INTO ledger(patient_id, unit_id, pass_num) VALUES(?,?,?)`, rel.PatientID, rel.UnitID, pass)
	}
	sort.Slice(releases, func(i, j int) bool {
		if releases[i].PatientID == releases[j].PatientID {
			return releases[i].UnitID < releases[j].UnitID
		}
		return releases[i].PatientID < releases[j].PatientID
	})
	digest := digestReleases(releases)
	rep := model.ReleaseReport{
		ScenarioID:     sid,
		EvaluationPass: pass,
		Releases:       releases,
		LedgerDigest:   digest,
	}
	raw, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if outPath == "" {
		outPath = "/app/output/release-ledger.json"
	}
	return os.WriteFile(outPath, raw, 0o644)
}

func buildReleases(db *sql.DB) ([]model.ReleaseLine, error) {
	patients, err := db.Query(`SELECT DISTINCT patient_id FROM crossmatch_rows ORDER BY patient_id`)
	if err != nil {
		return nil, err
	}
	defer patients.Close()
	var out []model.ReleaseLine
	for patients.Next() {
		var pid string
		if err := patients.Scan(&pid); err != nil {
			return nil, err
		}
		rel, err := firstCompatible(db, pid)
		if err != nil {
			return nil, err
		}
		if rel != nil {
			out = append(out, *rel)
		}
	}
	return out, patients.Err()
}

func firstCompatible(db *sql.DB, patientID string) (*model.ReleaseLine, error) {
	rs, err := db.Query(`
		SELECT c.unit_id, c.compatible, u.collected_at
		FROM crossmatch_rows c
		JOIN units u ON u.unit_id = c.unit_id
		WHERE c.patient_id=?
		ORDER BY u.collected_at ASC`, patientID)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	for rs.Next() {
		var unitID string
		var compat int
		var collected string
		if err := rs.Scan(&unitID, &compat, &collected); err != nil {
			return nil, err
		}
		if compat != 1 {
			continue
		}
		ov, _ := emergaudit.Lookup(db, patientID, unitID)
		line := model.ReleaseLine{
			PatientID: patientID, UnitID: unitID, ReleaseStatus: "approved",
			OverrideApplied: ov != nil, Authorizer: "", Reason: "",
		}
		if ov != nil {
			line.Authorizer = ov.Authorizer
			line.Reason = ov.Reason
		}
		return &line, nil
	}
	return nil, nil
}

func readPass() int {
	raw, err := os.ReadFile("/app/state/screening-pass.json")
	if err != nil {
		return 0
	}
	var body struct {
		EvaluationPass int `json:"screening_pass"`
	}
	if json.Unmarshal(raw, &body) != nil {
		return 0
	}
	return body.EvaluationPass
}

func digestReleases(lines []model.ReleaseLine) string {
	raw, _ := json.Marshal(lines)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}
