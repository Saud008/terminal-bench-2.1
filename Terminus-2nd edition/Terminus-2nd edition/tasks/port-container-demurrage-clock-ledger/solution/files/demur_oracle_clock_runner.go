package pauseclock

import (
	"time"

	"github.com/terminus/demurctl/internal/closurecal"
	"github.com/terminus/demurctl/internal/holdpolicy"
	"github.com/terminus/demurctl/internal/model"
)

func onHold(day string, holds []model.Hold) bool {
	for _, h := range holds {
		if day >= h.Start && day < h.End {
			return true
		}
	}
	return false
}

// EligibleDays returns calendar days that count toward free time and demurrage.
func EligibleDays(gateIn, endExclusive time.Time, holds []model.Hold, closures []model.Closure) []string {
	var days []string
	for d := gateIn; d.Before(endExclusive); d = d.AddDate(0, 0, 1) {
		day := d.Format("2006-01-02")
		if closurecal.IsExcluded(day, closures) {
			continue
		}
		if onHold(day, holds) {
			continue
		}
		days = append(days, day)
	}
	return days
}

func PeakActiveHold(holds []model.Hold, gateIn, endExclusive time.Time, closures []model.Closure) string {
	best := ""
	bestRank := -1
	for d := gateIn; d.Before(endExclusive); d = d.AddDate(0, 0, 1) {
		day := d.Format("2006-01-02")
		if closurecal.IsExcluded(day, closures) {
			continue
		}
		label := holdpolicy.PickActiveHold(holds, day)
		if label == "" {
			continue
		}
		rank := holdpolicy.RankOf(label)
		if rank > bestRank {
			bestRank = rank
			best = label
		}
	}
	return best
}
