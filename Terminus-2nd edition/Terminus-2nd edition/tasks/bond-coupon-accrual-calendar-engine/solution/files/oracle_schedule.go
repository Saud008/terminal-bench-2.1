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
		y, m, d := cur.Date()
		nm := int(m) + months
		ny := y
		for nm > 12 {
			nm -= 12
			ny++
		}
		last := daysInMonth(ny, time.Month(nm))
		day := d
		if day > last {
			day = last
		}
		next := time.Date(ny, time.Month(nm), day, 0, 0, 0, 0, time.UTC)
		if !next.Before(maturity) {
			break
		}
		out = append(out, next)
		cur = next
	}
	out = append(out, maturity)
	return out
}

func daysInMonth(y int, m time.Month) int {
	return time.Date(y, m+1, 0, 0, 0, 0, 0, time.UTC).Day()
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
