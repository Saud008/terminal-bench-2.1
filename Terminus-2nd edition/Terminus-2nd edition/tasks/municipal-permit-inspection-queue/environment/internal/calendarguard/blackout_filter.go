package calendarguard

import (
	"database/sql"
	"encoding/json"
	"os"

	"github.com/terminus/mpiqctl/internal/calendarblock"
	"github.com/terminus/mpiqctl/internal/permitstore"
)

func FilterBlackouts() error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	eligible, err := buildEligible(db)
	if err != nil {
		return err
	}
	raw, err := json.Marshal(eligible)
	if err != nil {
		return err
	}
	return os.WriteFile("/app/work/eligible-dates.json", append(raw, '\n'), 0o644)
}

func buildEligible(db *sql.DB) (map[string][]int, error) {
	rs, err := db.Query(`SELECT permit_id, district_id, requested_day FROM permits WHERE deferred=0`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	type row struct {
		id, district string
		day          int
	}
	var permits []row
	for rs.Next() {
		var r row
		if err := rs.Scan(&r.id, &r.district, &r.day); err != nil {
			return nil, err
		}
		permits = append(permits, r)
	}
	if err := rs.Err(); err != nil {
		return nil, err
	}
	out := map[string][]int{}
	for _, p := range permits {
		ok, err := dayEligible(db, p.district, p.day)
		if err != nil {
			return nil, err
		}
		if ok {
			out[p.id] = []int{p.day}
		}
	}
	return out, nil
}

func dayEligible(db *sql.DB, district string, day int) (bool, error) {
	rs, err := db.Query(`SELECT start_day, end_day FROM blackout_windows WHERE district_id=?`, district)
	if err != nil {
		return false, err
	}
	defer rs.Close()
	blocked := false
	for rs.Next() {
		var start, end int
		if err := rs.Scan(&start, &end); err != nil {
			return false, err
		}
		if calendarblock.DayBlocked(day, start, end) {
			blocked = true
		}
	}
	return !blocked, rs.Err()
}
