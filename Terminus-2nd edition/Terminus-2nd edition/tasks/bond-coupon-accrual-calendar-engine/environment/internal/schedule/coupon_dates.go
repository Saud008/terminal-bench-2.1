package schedule

import (
	"time"

	"github.com/terminus/bondacc/internal/calendar"
)

func CouponDates(issue, maturity time.Time, frequency int) []time.Time {
	if frequency <= 0 {
		frequency = 2
	}
	months := 12 / frequency
	var out []time.Time
	cur := issue
	for cur.Before(maturity) {
		next := cur.AddDate(0, months, 0)
		if !next.Before(maturity) {
			break
		}
		out = append(out, next)
		cur = next
	}
	out = append(out, maturity)
	return out
}

func PeriodContaining(settlement, issue time.Time, dates []time.Time) (start, end time.Time) {
	if len(dates) == 0 {
		return issue, settlement
	}
	prev := issue
	for _, cp := range dates {
		if settlement.Before(cp) {
			return prev, cp
		}
		prev = cp
	}
	return prev, dates[len(dates)-1]
}

func Parse(s string) time.Time {
	return calendar.ParseDate(s)
}
