package rrule

import (
	"time"

	"github.com/terminus/icalexpand/internal/model"
)

var weekday = map[string]time.Weekday{
	"SU": time.Sunday, "MO": time.Monday, "TU": time.Tuesday, "WE": time.Wednesday,
	"TH": time.Thursday, "FR": time.Friday, "SA": time.Saturday,
}

func expandWeekly(ev model.Event) []time.Time {
	start := ev.DTStart
	maxN := 128
	if ev.RRule.Count > 0 {
		maxN = ev.RRule.Count * 2
	}
	var out []time.Time
	cur := start
	for len(out) < maxN {
		for d := 0; d < 7; d++ {
			day := cur.AddDate(0, 0, d)
			if matchByDay(day, ev.RRule.ByDay) {
				out = append(out, day)
			}
		}
		cur = cur.AddDate(0, 0, 7*ev.RRule.Interval)
		if ev.RRule.Until != nil && cur.After(*ev.RRule.Until) {
			break
		}
	}
	return out
}

func matchByDay(t time.Time, byday []string) bool {
	if len(byday) == 0 {
		return true
	}
	wd := t.Weekday()
	for _, code := range byday {
		if weekday[code] == wd {
			return true
		}
	}
	return false
}

func monthDays(ev model.Event, month time.Time) []time.Time {
	first := time.Date(month.Year(), month.Month(), 1, ev.DTStart.Hour(), ev.DTStart.Minute(), ev.DTStart.Second(), 0, time.UTC)
	last := first.AddDate(0, 1, -1)
	var days []time.Time
	for d := first; !d.After(last); d = d.AddDate(0, 0, 1) {
		if matchByDay(d, ev.RRule.ByDay) {
			days = append(days, d)
		}
	}
	return days
}

func expandMonthly(ev model.Event) []time.Time {
	start := ev.DTStart
	cur := time.Date(start.Year(), start.Month(), 1, start.Hour(), start.Minute(), start.Second(), 0, time.UTC)
	var out []time.Time
	for i := 0; i < 36; i++ {
		days := monthDays(ev, cur)
		picked := pickBySetPos(days, ev.RRule.BySetPos)
		out = append(out, picked...)
		cur = cur.AddDate(0, ev.RRule.Interval, 0)
		if ev.RRule.Until != nil && cur.After(*ev.RRule.Until) {
			break
		}
	}
	return out
}
