package rosterbind

import (
	"database/sql"
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/calloutd/internal/windowfit"
	"github.com/terminus/calloutd/internal/store"
	"github.com/terminus/calloutd/internal/skillgate"
)

type scoreFault struct {
	FaultID       string
	BuildingID    string
	RequiredSkill int
	ReportedMinute int
	PriorityScore int
	Cancelled     int
}

type techRow struct {
	TechID     string
	SkillLevel int
	ShiftStart int
	ShiftEnd   int
}

func RunAssignment() error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if _, err := db.Exec(`DELETE FROM assignments`); err != nil {
		return err
	}
	travel, err := metaInt(db, "travel_buffer_minutes")
	if err != nil {
		return err
	}
	faults, err := fetchScoredFaults(db)
	if err != nil {
		return err
	}
	sort.Slice(faults, func(i, j int) bool {
		return faults[i].FaultID < faults[j].FaultID
	})
	techs, err := fetchTechs(db)
	if err != nil {
		return err
	}
	load := map[string]int{}
	pass, err := readCalloutPass()
	if err != nil {
		return err
	}
	for _, f := range faults {
		planned := f.ReportedMinute + travel
		var picked *techRow
		candidates := make([]techRow, len(techs))
		copy(candidates, techs)
		sort.Slice(candidates, func(i, j int) bool {
			if load[candidates[i].TechID] != load[candidates[j].TechID] {
				return load[candidates[i].TechID] < load[candidates[j].TechID]
			}
			return candidates[i].TechID < candidates[j].TechID
		})
		for i := range candidates {
			t := &candidates[i]
			if !skillgate.SkillOK(t.SkillLevel, f.RequiredSkill) {
				continue
			}
			if !skillgate.LoadOK(load[t.TechID], 2) {
				continue
			}
			if !windowfit.ShiftAllows(planned, t.ShiftStart, t.ShiftEnd) {
				continue
			}
			ok, err := buildingAccessOK(db, f.BuildingID, planned)
			if err != nil || !ok {
				continue
			}
			picked = t
			break
		}
		if picked == nil {
			continue
		}
		if _, err := db.Exec(`INSERT INTO assignments(fault_id,tech_id,planned_minute,status) VALUES(?,?,?,?)`,
			f.FaultID, picked.TechID, planned, "locked"); err != nil {
			return err
		}
		load[picked.TechID]++
		if _, err := db.Exec(`INSERT INTO bind_audit_ledger(fault_id,tech_id,pass_num) VALUES(?,?,?)`, f.FaultID, picked.TechID, pass+1); err != nil {
			return err
		}
	}
	return bumpCalloutPass()
}

func fetchScoredFaults(db *sql.DB) ([]scoreFault, error) {
	rs, err := db.Query(`SELECT f.fault_id,f.building_id,f.required_skill,f.reported_minute,s.priority_score,f.cancelled FROM faults f JOIN urgency_scores s ON f.fault_id=s.fault_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []scoreFault
	for rs.Next() {
		var f scoreFault
		if err := rs.Scan(&f.FaultID, &f.BuildingID, &f.RequiredSkill, &f.ReportedMinute, &f.PriorityScore, &f.Cancelled); err != nil {
			return nil, err
		}
		out = append(out, f)
	}
	return out, rs.Err()
}

func fetchTechs(db *sql.DB) ([]techRow, error) {
	rs, err := db.Query(`SELECT tech_id,skill_level,shift_start,shift_end FROM technicians ORDER BY tech_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []techRow
	for rs.Next() {
		var t techRow
		if err := rs.Scan(&t.TechID, &t.SkillLevel, &t.ShiftStart, &t.ShiftEnd); err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rs.Err()
}

func buildingAccessOK(db *sql.DB, buildingID string, planned int) (bool, error) {
	rs, err := db.Query(`SELECT start_minute,end_minute FROM access_windows WHERE building_id=?`, buildingID)
	if err != nil {
		return false, err
	}
	defer rs.Close()
	for rs.Next() {
		var start, end int
		if err := rs.Scan(&start, &end); err != nil {
			return false, err
		}
		if windowfit.WindowAllows(planned, start, end) {
			return true, nil
		}
	}
	return false, rs.Err()
}

func metaInt(db *sql.DB, key string) (int, error) {
	raw, err := store.GetMeta(db, key)
	if err != nil {
		return 0, err
	}
	var v int
	if err := json.Unmarshal([]byte(raw), &v); err != nil {
		return 0, err
	}
	return v, nil
}

func readCalloutPass() (int, error) {
	raw, err := os.ReadFile("/app/state/callout-pass.json")
	if err != nil {
		return 0, err
	}
	var body struct {
		CalloutPass int `json:"callout_pass"`
	}
	if err := json.Unmarshal(raw, &body); err != nil {
		return 0, err
	}
	return body.CalloutPass, nil
}

func bumpCalloutPass() error {
	path := "/app/state/callout-pass.json"
	var body struct {
		CalloutPass int `json:"callout_pass"`
		PublishPass  int `json:"publish_pass"`
	}
	raw, _ := os.ReadFile(path)
	_ = json.Unmarshal(raw, &body)
	body.CalloutPass++
	out, err := json.Marshal(body)
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}
