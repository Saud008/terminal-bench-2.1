package bundleload

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/mpiqctl/internal/model"
	"github.com/terminus/mpiqctl/internal/permitstore"
)

func LoadBundle(scenario, fixtureDir string) (*model.Bundle, error) {
	path := filepath.Join(fixtureDir, "scenarios", scenario, "bundle.json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var b model.Bundle
	if err := json.Unmarshal(raw, &b); err != nil {
		return nil, err
	}
	return &b, nil
}

func PersistBundle(b *model.Bundle) error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	tables := []string{"permits", "inspectors", "zoning_holds", "blackout_windows", "violations", "permit_routes", "queue_scores", "queue_entries", "bind_audit_ledger"}
	for _, t := range tables {
		if _, err := db.Exec("DELETE FROM " + t); err != nil {
			return err
		}
	}
	if err := store.SetMeta(db, "scenario_id", b.Scenario); err != nil {
		return err
	}
	epoch, _ := json.Marshal(b.PlanningEpochDay)
	if err := store.SetMeta(db, "planning_epoch_day", string(epoch)); err != nil {
		return err
	}
	for _, p := range b.Permits {
		def := 0
		if p.Deferred {
			def = 1
		}
		if _, err := db.Exec(`INSERT INTO permits(permit_id,district_id,permit_type,base_priority,requested_day,deferred) VALUES(?,?,?,?,?,?)`,
			p.PermitID, p.DistrictID, p.PermitType, p.BasePriority, p.RequestedDay, def); err != nil {
			return err
		}
	}
	for _, ins := range b.Inspectors {
		dists, _ := json.Marshal(ins.Districts)
		if _, err := db.Exec(`INSERT INTO inspectors(inspector_id,cert_level,districts,daily_cap,available_day) VALUES(?,?,?,?,?)`,
			ins.InspectorID, ins.CertLevel, string(dists), ins.DailyCap, ins.AvailableDay); err != nil {
			return err
		}
	}
	for _, h := range b.ZoningHolds {
		active := 0
		if h.Active {
			active = 1
		}
		if _, err := db.Exec(`INSERT INTO zoning_holds(district_id,hold_rank,active,reason_code) VALUES(?,?,?,?)`,
			h.DistrictID, h.HoldRank, active, h.ReasonCode); err != nil {
			return err
		}
	}
	for _, bw := range b.BlackoutWindows {
		if _, err := db.Exec(`INSERT INTO blackout_windows(district_id,start_day,end_day) VALUES(?,?,?)`,
			bw.DistrictID, bw.StartDay, bw.EndDay); err != nil {
			return err
		}
	}
	for _, v := range b.Violations {
		if _, err := db.Exec(`INSERT INTO violations(permit_id,severity,days_ago) VALUES(?,?,?)`,
			v.PermitID, v.Severity, v.DaysAgo); err != nil {
			return err
		}
	}
	for _, r := range b.PermitRoutes {
		if _, err := db.Exec(`INSERT INTO permit_routes(permit_type,inspection_lane,min_cert_level) VALUES(?,?,?)`,
			r.PermitType, r.InspectionLane, r.MinCertLevel); err != nil {
			return err
		}
	}
	return nil
}

func BundleLoaded(scenario string) error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	sid, err := store.GetMeta(db, "scenario_id")
	if err != nil || sid != scenario {
		return fmt.Errorf("snapshot not loaded for %s", scenario)
	}
	return nil
}
