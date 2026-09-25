package daycount

import (
	"time"
)

func YearFraction(start, end time.Time, convention string) float64 {
	if !end.After(start) {
		return 0
	}
	switch convention {
	case "ACT/360":
		days := end.Sub(start).Hours() / 24
		return days / 365.0
	case "30/360":
		return thirt360(start, end)
	case "ACT/ACT":
		return actAct(start, end)
	default:
		return 0
	}
}

func thirt360(start, end time.Time) float64 {
	y1, m1, d1 := start.Date()
	y2, m2, d2 := end.Date()
	if d1 == 31 {
		d1 = 30
	}
	if d2 == 31 && d1 == 30 {
		d2 = 30
	}
	days := (y2-y1)*360 + int(m2-m1)*30 + (d2 - d1)
	return float64(days) / 360.0
}

func actAct(start, end time.Time) float64 {
	days := end.Sub(start).Hours() / 24
	denom := 365.0
	if containsLeapDay(start, end) {
		denom = 366.0
	}
	return days / denom
}

func containsLeapDay(a, b time.Time) bool {
	for y := a.Year(); y <= b.Year(); y++ {
		leap := time.Date(y, 2, 29, 0, 0, 0, 0, time.UTC)
		if !leap.Before(a) && leap.Before(b) {
			return true
		}
	}
	return false
}

func AccruedCents(face int64, couponBPS int, yf float64) int64 {
	raw := float64(face) * float64(couponBPS) / 10000.0 * yf
	if raw < 0 {
		return 0
	}
	return int64(raw + 0.5)
}
