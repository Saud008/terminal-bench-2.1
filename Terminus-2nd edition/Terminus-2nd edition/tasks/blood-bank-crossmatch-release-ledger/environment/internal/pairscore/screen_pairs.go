package pairscore

import (
	"database/sql"
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/bbreleasectl/internal/hemcompat"
	"github.com/terminus/bbreleasectl/internal/immuno"
	"github.com/terminus/bbreleasectl/internal/shelflife"
	"github.com/terminus/bbreleasectl/internal/model"
	"github.com/terminus/bbreleasectl/internal/emergaudit"
	"github.com/terminus/bbreleasectl/internal/matrixstage"
	"github.com/terminus/bbreleasectl/internal/persist"
)

type patientRow struct {
	ID          string
	ABO         string
	Rh          string
	Antibodies  []string
}

type unitRow struct {
	ID          string
	ABO         string
	Rh          string
	CollectedAt string
	ExpiresAt   string
	Antigens    []string
}

func RunEvaluation(scenario string) error {
	db, err := persist.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if _, err := db.Exec(`DELETE FROM crossmatch_rows`); err != nil {
		return err
	}
	clock, err := persist.GetMeta(db, "release_clock")
	if err != nil {
		return err
	}
	patients, err := loadPatients(db)
	if err != nil {
		return err
	}
	units, err := loadUnits(db)
	if err != nil {
		return err
	}
	order := make([]matrixstage.UnitSlot, len(units))
	for i, u := range units {
		order[i] = matrixstage.UnitSlot{UnitID: u.ID, CollectedAt: u.CollectedAt}
	}
	matrixstage.SortUnits(order)
	unitByID := map[string]unitRow{}
	for _, u := range units {
		unitByID[u.ID] = u
	}
	var rows []model.CrossmatchRow
	for _, p := range patients {
		for _, slot := range order {
			u := unitByID[slot.UnitID]
			row := evaluatePair(db, p, u, clock)
			rows = append(rows, row)
			codes, _ := json.Marshal(row.FailureCodes)
			compat := 0
			if row.Compatible {
				compat = 1
			}
			if _, err := db.Exec(`INSERT INTO crossmatch_rows(patient_id,unit_id,compatible,failure_codes) VALUES(?,?,?,?)`,
				row.PatientID, row.UnitID, compat, string(codes)); err != nil {
				return err
			}
		}
	}
	return writeStaging(scenario, rows)
}

func evaluatePair(db *sql.DB, p patientRow, u unitRow, clock string) model.CrossmatchRow {
	row := model.CrossmatchRow{PatientID: p.ID, UnitID: u.ID, Compatible: true, FailureCodes: []string{}}
	if !hemcompat.ABOCompatible(p.ABO, u.ABO) {
		row.Compatible = false
		row.FailureCodes = append(row.FailureCodes, "abo_mismatch")
	}
	rhOK := hemcompat.RhCompatible(p.Rh, u.Rh)
	if !rhOK {
		ov, _ := emergaudit.Lookup(db, p.ID, u.ID)
		if ov == nil {
			row.Compatible = false
			row.FailureCodes = append(row.FailureCodes, "rh_mismatch")
		}
	}
	if immuno.UnitBlocked(p.Antibodies, u.Antigens) {
		row.Compatible = false
		row.FailureCodes = append(row.FailureCodes, "antibody_conflict")
	}
	if shelflife.UnitExpired(clock, u.CollectedAt, u.ExpiresAt) {
		row.Compatible = false
		row.FailureCodes = append(row.FailureCodes, "unit_expired")
	}
	return row
}

func loadPatients(db *sql.DB) ([]patientRow, error) {
	rs, err := db.Query(`SELECT patient_id, abo, rh FROM patients ORDER BY patient_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []patientRow
	for rs.Next() {
		var p patientRow
		if err := rs.Scan(&p.ID, &p.ABO, &p.Rh); err != nil {
			return nil, err
		}
		abRs, err := db.Query(`SELECT antibody FROM patient_antibodies WHERE patient_id=?`, p.ID)
		if err != nil {
			return nil, err
		}
		for abRs.Next() {
			var ab string
			if err := abRs.Scan(&ab); err != nil {
				abRs.Close()
				return nil, err
			}
			p.Antibodies = append(p.Antibodies, ab)
		}
		abRs.Close()
		out = append(out, p)
	}
	return out, rs.Err()
}

func loadUnits(db *sql.DB) ([]unitRow, error) {
	rs, err := db.Query(`SELECT unit_id, abo, rh, collected_at, expires_at FROM units ORDER BY unit_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []unitRow
	for rs.Next() {
		var u unitRow
		if err := rs.Scan(&u.ID, &u.ABO, &u.Rh, &u.CollectedAt, &u.ExpiresAt); err != nil {
			return nil, err
		}
		agRs, err := db.Query(`SELECT antigen FROM unit_antigens WHERE unit_id=?`, u.ID)
		if err != nil {
			return nil, err
		}
		for agRs.Next() {
			var ag string
			if err := agRs.Scan(&ag); err != nil {
				agRs.Close()
				return nil, err
			}
			u.Antigens = append(u.Antigens, ag)
		}
		agRs.Close()
		out = append(out, u)
	}
	return out, rs.Err()
}

func writeStaging(scenario string, rows []model.CrossmatchRow) error {
	dir := "/app/work/compatibility-matrix"
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	f, err := os.Create(filepath.Join(dir, scenario+".jsonl"))
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	for _, row := range rows {
		if err := enc.Encode(row); err != nil {
			return err
		}
	}
	return nil
}
