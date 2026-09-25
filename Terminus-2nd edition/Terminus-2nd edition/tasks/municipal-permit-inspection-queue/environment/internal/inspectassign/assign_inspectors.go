package inspectassign

import (
	"database/sql"
	"encoding/json"
	"os"
	"sort"
	"strings"

	"github.com/terminus/mpiqctl/internal/credmatch"
	"github.com/terminus/mpiqctl/internal/permitstore"
)

type scoredPermit struct {
	ID, District, PermitType string
	CompositeScore           int
	RequestedDay             int
	HoldBlocked              int
}

type inspectorRow struct {
	ID         string
	CertLevel  int
	Districts  []string
	DailyCap   int
	AvailDay   int
}

func RunBinding() error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if _, err := db.Exec(`DELETE FROM queue_entries`); err != nil {
		return err
	}
	permits, err := fetchScoredPermits(db)
	if err != nil {
		return err
	}
	sort.Slice(permits, func(i, j int) bool {
		if permits[i].CompositeScore != permits[j].CompositeScore {
			return permits[i].CompositeScore > permits[j].CompositeScore
		}
		return permits[i].ID < permits[j].ID
	})
	inspectors, err := fetchInspectors(db)
	if err != nil {
		return err
	}
	load := map[string]int{}
	pass, err := readQueuePass()
	if err != nil {
		return err
	}
	for _, p := range permits {
		if p.HoldBlocked != 0 || p.CompositeScore <= 0 {
			continue
		}
		lane, minCert, err := routeForPermit(db, p.PermitType)
		if err != nil {
			return err
		}
		scheduled := p.RequestedDay
		var picked *inspectorRow
		candidates := make([]inspectorRow, len(inspectors))
		copy(candidates, inspectors)
		sort.Slice(candidates, func(i, j int) bool {
			if load[candidates[i].ID] != load[candidates[j].ID] {
				return load[candidates[i].ID] < load[candidates[j].ID]
			}
			return candidates[i].ID < candidates[j].ID
		})
		for i := range candidates {
			ins := &candidates[i]
			if !credmatch.CertOK(ins.CertLevel, minCert) {
				continue
			}
			if !credmatch.CapOK(load[ins.ID], ins.DailyCap) {
				continue
			}
			if !districtCovers(ins.Districts, p.District) {
				continue
			}
			if scheduled < ins.AvailDay {
				continue
			}
			picked = ins
			break
		}
		if picked == nil {
			continue
		}
		if _, err := db.Exec(`INSERT INTO queue_entries(permit_id,inspector_id,scheduled_day,inspection_lane,status) VALUES(?,?,?,?,?)`,
			p.ID, picked.ID, scheduled, lane, "queued"); err != nil {
			return err
		}
		load[picked.ID]++
		if _, err := db.Exec(`INSERT INTO bind_audit_ledger(permit_id,inspector_id,pass_num) VALUES(?,?,?)`, p.ID, picked.ID, pass+1); err != nil {
			return err
		}
	}
	return nil
}

func fetchScoredPermits(db *sql.DB) ([]scoredPermit, error) {
	rs, err := db.Query(`SELECT p.permit_id,p.district_id,p.permit_type,p.requested_day,s.composite_score,s.hold_blocked FROM permits p JOIN queue_scores s ON p.permit_id=s.permit_id WHERE p.deferred=0`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []scoredPermit
	for rs.Next() {
		var p scoredPermit
		if err := rs.Scan(&p.ID, &p.District, &p.PermitType, &p.RequestedDay, &p.CompositeScore, &p.HoldBlocked); err != nil {
			return nil, err
		}
		out = append(out, p)
	}
	return out, rs.Err()
}

func fetchInspectors(db *sql.DB) ([]inspectorRow, error) {
	rs, err := db.Query(`SELECT inspector_id,cert_level,districts,daily_cap,available_day FROM inspectors ORDER BY inspector_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []inspectorRow
	for rs.Next() {
		var ins inspectorRow
		var distRaw string
		if err := rs.Scan(&ins.ID, &ins.CertLevel, &distRaw, &ins.DailyCap, &ins.AvailDay); err != nil {
			return nil, err
		}
		_ = json.Unmarshal([]byte(distRaw), &ins.Districts)
		out = append(out, ins)
	}
	return out, rs.Err()
}

func routeForPermit(db *sql.DB, permitType string) (string, int, error) {
	var lane string
	var floor int
	err := db.QueryRow(`SELECT inspection_lane, min_cert_level FROM permit_routes WHERE permit_type=?`, permitType).Scan(&lane, &floor)
	if err == sql.ErrNoRows {
		return "lane-general", 1, nil
	}
	return lane, floor, err
}

func districtCovers(districts []string, target string) bool {
	for _, d := range districts {
		if d == target || d == "*" {
			return true
		}
	}
	return false
}

func readQueuePass() (int, error) {
	raw, err := os.ReadFile("/app/state/queue-pass.json")
	if err != nil {
		return 0, err
	}
	var body struct {
		QueuePass int `json:"queue_pass"`
	}
	if err := json.Unmarshal(raw, &body); err != nil {
		return 0, err
	}
	return body.QueuePass, nil
}

func InspectorDistrictsCSV(districts []string) string {
	return strings.Join(districts, ",")
}
