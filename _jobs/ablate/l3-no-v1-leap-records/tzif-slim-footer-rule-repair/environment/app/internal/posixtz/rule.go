package posixtz

import "shiftclock/internal/civil"

// yearDay returns the zero-based day of year (0 = January 1) that r names in
// year y.
func (r Rule) yearDay(y int64) int {
	switch r.Kind {
	case JulianNoLeap:
		return r.Day - 1
	case ZeroBased:
		return r.Day
	default:
		first := civil.DaysFromCivil(y, r.Month, 1)
		day := 1 + (r.Weekday-civil.Weekday(first)+7)%7 + (r.Week-1)*7
		return int(first - civil.DaysFromCivil(y, 1, 1) + int64(day-1))
	}
}

// Instant returns the UTC time of the transition r names in year y, given
// the UTC offset in effect just before the transition.
func (r Rule) Instant(y int64, before int64) int64 {
	days := civil.DaysFromCivil(y, 1, 1) + int64(r.yearDay(y))
	return days*civil.SecondsPerDay + r.Time - before
}
