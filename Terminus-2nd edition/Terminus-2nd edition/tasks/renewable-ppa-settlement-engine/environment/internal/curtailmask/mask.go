package curtailmask

import (
	"time"

	"github.com/terminus/ppareconctl/internal/model"
)

// ActiveDuring returns true when ts falls inside a curtailment window.
// Contract: half-open interval [start, end).
func ActiveDuring(ts string, windows []model.Curtailment) (bool, error) {
	when, err := time.Parse(time.RFC3339, ts)
	if err != nil {
		return false, err
	}
	when = when.UTC()
	for _, w := range windows {
		start, err := time.Parse(time.RFC3339, w.StartUTC)
		if err != nil {
			return false, err
		}
		end, err := time.Parse(time.RFC3339, w.EndUTC)
		if err != nil {
			return false, err
		}
		start = start.UTC()
		end = end.UTC()
		if !when.Before(start) && !when.After(end) {
			return true, nil
		}
	}
	return false, nil
}
