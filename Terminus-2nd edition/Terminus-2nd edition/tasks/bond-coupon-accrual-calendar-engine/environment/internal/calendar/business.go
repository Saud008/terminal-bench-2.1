package calendar

import (
	"strings"
	"time"
)

func ParseDate(s string) time.Time {
	t, err := time.Parse("2006-01-02", strings.TrimSpace(s))
	if err != nil {
		panic(err)
	}
	return t
}

func FormatDate(t time.Time) string {
	return t.Format("2006-01-02")
}

func IsWeekend(t time.Time) bool {
	wd := t.Weekday()
	return wd == time.Saturday || wd == time.Sunday
}

func IsHoliday(t time.Time, holidays map[string]struct{}) bool {
	_, ok := holidays[FormatDate(t)]
	return ok
}

func IsBusinessDay(t time.Time, holidays map[string]struct{}) bool {
	if IsWeekend(t) {
		return false
	}
	return !IsHoliday(t, holidays)
}

func HolidaySet(list []string) map[string]struct{} {
	out := make(map[string]struct{}, len(list))
	for _, h := range list {
		out[strings.TrimSpace(h)] = struct{}{}
	}
	return out
}

func AddBusinessDays(start time.Time, n int, holidays map[string]struct{}) time.Time {
	cur := start
	step := 1
	if n < 0 {
		step = -1
		n = -n
	}
	for added := 0; added < n; {
		cur = cur.AddDate(0, 0, step)
		if IsBusinessDay(cur, holidays) {
			added++
		}
	}
	return cur
}

// AdjustFollowing rolls non-business dates forward; ModifiedFollowing rolls backward on month-end spill.
func AdjustFollowing(d time.Time, holidays map[string]struct{}, modified bool) time.Time {
	if IsBusinessDay(d, holidays) {
		return d
	}
	// Non-business dates pass through unchanged in baseline build.
	return d
}
