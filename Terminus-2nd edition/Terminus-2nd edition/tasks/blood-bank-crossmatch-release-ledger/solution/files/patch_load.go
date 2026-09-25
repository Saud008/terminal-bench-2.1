package panelimport

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/bbreleasectl/internal/model"
	"github.com/terminus/bbreleasectl/internal/persist"
)

func LoadScenarioFile(scenario, fixtureDir string) (*model.Scenario, error) {
	path := filepath.Join(fixtureDir, "scenarios", scenario+".json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var sc model.Scenario
	if err := json.Unmarshal(raw, &sc); err != nil {
		return nil, err
	}
	if clk := os.Getenv("TB3_RELEASE_CLOCK"); clk != "" {
		sc.ReleaseClock = clk
	}
	return &sc, nil
}

func PersistScenario(sc *model.Scenario) error {
	db, err := persist.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	tables := []string{"patient_antibodies", "unit_antigens", "overrides", "crossmatch_rows", "ledger", "units", "patients"}
	for _, t := range tables {
		if _, err := db.Exec("DELETE FROM " + t); err != nil {
			return err
		}
	}
	if err := persist.SetMeta(db, "scenario_id", sc.ScenarioID); err != nil {
		return err
	}
	if err := persist.SetMeta(db, "release_clock", sc.ReleaseClock); err != nil {
		return err
	}
	for _, p := range sc.Patients {
		if _, err := db.Exec(`INSERT INTO patients(patient_id,abo,rh) VALUES(?,?,?)`, p.PatientID, p.ABO, p.Rh); err != nil {
			return err
		}
		for _, ab := range p.Antibodies {
			if _, err := db.Exec(`INSERT INTO patient_antibodies(patient_id,antibody) VALUES(?,?)`, p.PatientID, ab); err != nil {
				return err
			}
		}
	}
	for _, u := range sc.Units {
		if _, err := db.Exec(`INSERT INTO units(unit_id,abo,rh,collected_at,expires_at) VALUES(?,?,?,?,?)`,
			u.UnitID, u.ABO, u.Rh, u.CollectedAt, u.ExpiresAt); err != nil {
			return err
		}
		for _, ag := range u.Antigens {
			if _, err := db.Exec(`INSERT INTO unit_antigens(unit_id,antigen) VALUES(?,?)`, u.UnitID, ag); err != nil {
				return err
			}
		}
	}
	for _, o := range sc.Overrides {
		if _, err := db.Exec(`INSERT INTO overrides(patient_id,unit_id,authorizer,reason,issued_at) VALUES(?,?,?,?,?)`,
			o.PatientID, o.UnitID, o.Authorizer, o.Reason, o.IssuedAt); err != nil {
			return err
		}
	}
	return nil
}

func ScenarioLoaded(scenario string) error {
	db, err := persist.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	sid, err := persist.GetMeta(db, "scenario_id")
	if err != nil || sid != scenario {
		return fmt.Errorf("scenario not loaded for %s", scenario)
	}
	return nil
}
