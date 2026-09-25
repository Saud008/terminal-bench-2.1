package rosterfeed

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/calloutd/internal/model"
	"github.com/terminus/calloutd/internal/store"
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
	tables := []string{"faults", "technicians", "access_windows", "sla_contracts", "urgency_scores", "assignments", "bind_audit_ledger"}
	for _, t := range tables {
		if _, err := db.Exec("DELETE FROM " + t); err != nil {
			return err
		}
	}
	if err := store.SetMeta(db, "scenario_id", b.Scenario); err != nil {
		return err
	}
	anchor, _ := json.Marshal(b.RosterEpochMinute)
	if err := store.SetMeta(db, "roster_epoch_minute", string(anchor)); err != nil {
		return err
	}
	buf, _ := json.Marshal(b.TravelBufferMinutes)
	if err := store.SetMeta(db, "travel_buffer_minutes", string(buf)); err != nil {
		return err
	}
	for _, f := range b.Faults {
		c := 0
		if f.Cancelled {
			c = 1
		}
		if _, err := db.Exec(`INSERT INTO faults(fault_id,building_id,elevator_bank,fault_code,severity_base,trapped_passengers,reported_minute,required_skill,cancelled) VALUES(?,?,?,?,?,?,?,?,?)`,
			f.FaultID, f.BuildingID, f.ElevatorBank, f.FaultCode, f.SeverityBase, f.TrappedPassengers, f.ReportedMinute, f.RequiredSkill, c); err != nil {
			return err
		}
	}
	for _, t := range b.Technicians {
		tags, _ := json.Marshal(t.CertTags)
		if _, err := db.Exec(`INSERT INTO technicians(tech_id,skill_level,shift_start,shift_end,cert_tags) VALUES(?,?,?,?,?)`,
			t.TechID, t.SkillLevel, t.ShiftStart, t.ShiftEnd, string(tags)); err != nil {
			return err
		}
	}
	for _, bld := range b.Buildings {
		for _, w := range bld.AccessWindows {
			if _, err := db.Exec(`INSERT INTO access_windows(building_id,start_minute,end_minute) VALUES(?,?,?)`,
				bld.BuildingID, w.StartMinute, w.EndMinute); err != nil {
				return err
			}
		}
	}
	for _, s := range b.SLAContracts {
		if _, err := db.Exec(`INSERT INTO sla_contracts(tier,building_id,max_response_minutes,escalation_weight,tier_rank) VALUES(?,?,?,?,?)`,
			s.Tier, s.BuildingID, s.MaxResponseMinutes, s.EscalationWeight, s.TierRank); err != nil {
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
		return fmt.Errorf("bundle not loaded for %s", scenario)
	}
	return nil
}
