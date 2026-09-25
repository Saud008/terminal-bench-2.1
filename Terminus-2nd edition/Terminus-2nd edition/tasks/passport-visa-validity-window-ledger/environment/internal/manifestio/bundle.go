package manifestio

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/borderdocctl/internal/model"
	"github.com/terminus/borderdocctl/internal/store"
)

func LoadScenario(scenario, fixtureDir string) (*model.Scenario, error) {
	path := filepath.Join(fixtureDir, "scenarios", scenario+".json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var sc model.Scenario
	if err := json.Unmarshal(raw, &sc); err != nil {
		return nil, err
	}
	return &sc, nil
}

func PersistBundle(sc *model.Scenario) error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()

	tables := []string{"passports", "visas", "stamps", "rules", "holds", "decisions", "ledger"}
	for _, t := range tables {
		if _, err := db.Exec(`DELETE FROM ` + t); err != nil {
			return err
		}
	}

	if err := store.SetMeta(db, "scenario_id", sc.ScenarioID); err != nil {
		return err
	}
	if err := store.SetMeta(db, "reference_date", sc.ReferenceDate); err != nil {
		return err
	}
	if err := store.SetMeta(db, "grace_days", fmt.Sprintf("%d", sc.GraceDays)); err != nil {
		return err
	}

	for _, p := range sc.Passports {
		rev := 0
		if p.Revoked {
			rev = 1
		}
		if _, err := db.Exec(`INSERT INTO passports(doc_id,holder_id,issue_date,expiry_date,revoked) VALUES(?,?,?,?,?)`,
			p.DocID, p.HolderID, p.IssueDate, p.ExpiryDate, rev); err != nil {
			return err
		}
	}
	for _, v := range sc.Visas {
		rev := 0
		if v.Revoked {
			rev = 1
		}
		if _, err := db.Exec(`INSERT INTO visas(doc_id,passport_id,valid_from,valid_to,visa_class,revoked) VALUES(?,?,?,?,?,?)`,
			v.DocID, v.PassportID, v.ValidFrom, v.ValidTo, v.VisaClass, rev); err != nil {
			return err
		}
	}
	for _, st := range sc.Stamps {
		if _, err := db.Exec(`INSERT INTO stamps(stamp_id,passport_id,entry_date,exit_date,port_code) VALUES(?,?,?,?,?)`,
			st.StampID, st.PassportID, st.EntryDate, st.ExitDate, st.PortCode); err != nil {
			return err
		}
	}
	for _, r := range sc.Rules {
		if _, err := db.Exec(`INSERT INTO rules(rule_id,scope,port_code,max_stay_days) VALUES(?,?,?,?)`,
			r.RuleID, r.Scope, r.PortCode, r.MaxStayDays); err != nil {
			return err
		}
	}
	for _, h := range sc.Holds {
		active := 0
		if h.Active {
			active = 1
		}
		if _, err := db.Exec(`INSERT INTO holds(hold_id,holder_id,active,reason) VALUES(?,?,?,?)`,
			h.HoldID, h.HolderID, active, h.Reason); err != nil {
			return err
		}
	}

	snap := map[string]any{
		"scenario_id":    sc.ScenarioID,
		"reference_date": sc.ReferenceDate,
		"passport_count": len(sc.Passports),
		"visa_count":     len(sc.Visas),
		"stamp_count":    len(sc.Stamps),
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile("/app/state/manifest-snapshot.json", raw, 0o644)
}

func BundleLoaded(scenario string) error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	sid, err := store.GetMeta(db, "scenario_id")
	if err != nil || sid != scenario {
		return fmt.Errorf("bundle not loaded for %s", scenario)
	}
	return nil
}
