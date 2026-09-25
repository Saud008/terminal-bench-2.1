package rankengine

import (
	"database/sql"
	"encoding/json"
	"os"

	"github.com/terminus/mpiqctl/internal/calendarblock"
	"github.com/terminus/mpiqctl/internal/districtgate"
	"github.com/terminus/mpiqctl/internal/permitstore"
	"github.com/terminus/mpiqctl/internal/priorscore"
	"github.com/terminus/mpiqctl/internal/zoninghold"
)

func RunScoring() error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if _, err := db.Exec(`DELETE FROM queue_scores`); err != nil {
		return err
	}
	mask, err := loadHoldMask()
	if err != nil {
		return err
	}
	permits, err := fetchPermits(db)
	if err != nil {
		return err
	}
	for _, p := range permits {
		if !dayEligible(db, p.District, p.RequestedDay) {
			continue
		}
		violSum := violationSum(db, p.ID)
		comp := priorscore.CompositeScore(p.BasePriority, violSum)
		dHold := districtgate.DistrictHoldRank(mask, p.District)
		blocked := 0
		if zoninghold.BlocksPermit(0, dHold) {
			blocked = 1
			comp = 0
		}
		if blocked != 0 {
			if _, err := db.Exec(`INSERT INTO queue_scores(permit_id,composite_score,violation_weight,hold_blocked) VALUES(?,?,?,?)`,
				p.ID, comp, violSum, blocked); err != nil {
				return err
			}
			continue
		}
		if _, err := db.Exec(`INSERT INTO queue_scores(permit_id,composite_score,violation_weight,hold_blocked) VALUES(?,?,?,?)`,
			p.ID, comp, violSum, blocked); err != nil {
			return err
		}
	}
	ranks := map[string]int{}
	rs, err := db.Query(`SELECT permit_id, composite_score FROM queue_scores ORDER BY composite_score DESC, permit_id`)
	if err != nil {
		return err
	}
	defer rs.Close()
	for rs.Next() {
		var id string
		var score int
		if err := rs.Scan(&id, &score); err != nil {
			return err
		}
		ranks[id] = score
	}
	raw, err := json.Marshal(ranks)
	if err != nil {
		return err
	}
	if err := os.WriteFile("/app/work/violation-ranks.json", append(raw, '\n'), 0o644); err != nil {
		return err
	}
	return bumpQueuePass()
}

type permitRow struct {
	ID, District string
	BasePriority int
	RequestedDay int
}

func fetchPermits(db *sql.DB) ([]permitRow, error) {
	rs, err := db.Query(`SELECT permit_id, district_id, base_priority, requested_day FROM permits WHERE deferred=0`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []permitRow
	for rs.Next() {
		var p permitRow
		if err := rs.Scan(&p.ID, &p.District, &p.BasePriority, &p.RequestedDay); err != nil {
			return nil, err
		}
		out = append(out, p)
	}
	return out, rs.Err()
}

func dayEligible(db *sql.DB, district string, day int) bool {
	rs, err := db.Query(`SELECT start_day, end_day FROM blackout_windows WHERE district_id=?`, district)
	if err != nil {
		return true
	}
	defer rs.Close()
	for rs.Next() {
		var start, end int
		if err := rs.Scan(&start, &end); err != nil {
			return false
		}
		if calendarblock.DayBlocked(day, start, end) {
			return false
		}
	}
	return true
}

func violationSum(db *sql.DB, permitID string) int {
	rs, err := db.Query(`SELECT severity, days_ago FROM violations WHERE permit_id=?`, permitID)
	if err != nil {
		return 0
	}
	defer rs.Close()
	sum := 0
	for rs.Next() {
		var sev, ago int
		if err := rs.Scan(&sev, &ago); err != nil {
			return 0
		}
		sum += sev * priorscore.RecencyWeight(ago)
	}
	return sum
}

func loadHoldMask() (map[string]int, error) {
	raw, err := os.ReadFile("/app/work/hold-mask.json")
	if err != nil {
		return map[string]int{}, nil
	}
	var mask map[string]int
	if err := json.Unmarshal(raw, &mask); err != nil {
		return nil, err
	}
	return mask, nil
}

func bumpQueuePass() error {
	path := "/app/state/queue-pass.json"
	var body struct {
		QueuePass   int `json:"queue_pass"`
		PublishPass int `json:"publish_pass"`
	}
	raw, _ := os.ReadFile(path)
	_ = json.Unmarshal(raw, &body)
	body.QueuePass++
	out, err := json.Marshal(body)
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}
