package merge

import (
	"time"

	"github.com/harbor/tug-berth/internal/db"
)

// ApplyTotals returns the maximum single-assignment dwell per berth.
func ApplyTotals(assignments []db.Assignment) map[string]int {
	totals := map[string]int{}
	for _, a := range assignments {
		d := dwellMinutes(a.ArrivalUTC, a.DepartureUTC)
		if d > totals[a.BerthID] {
			totals[a.BerthID] = d
		}
	}
	return totals
}

func dwellMinutes(arrival, departure string) int {
	start, err1 := time.Parse(time.RFC3339, arrival)
	end, err2 := time.Parse(time.RFC3339, departure)
	if err1 != nil || err2 != nil {
		return 0
	}
	m := int(end.Sub(start).Minutes())
	if m < 0 {
		return 0
	}
	return m
}
