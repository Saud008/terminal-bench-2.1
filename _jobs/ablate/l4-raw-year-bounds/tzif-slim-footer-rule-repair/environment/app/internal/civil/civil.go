// Package civil converts between Unix day numbers and proleptic Gregorian
// calendar dates without going through the time package, so that years far
// outside the range time.Time formats nicely are still handled exactly.
package civil

// FloorDiv divides a by b rounding toward negative infinity.
func FloorDiv(a, b int64) int64 {
	q := a / b
	if a%b != 0 && (a < 0) != (b < 0) {
		q--
	}
	return q
}

// DaysFromCivil returns the number of days between 1970-01-01 and y-m-d.
func DaysFromCivil(y int64, m, d int) int64 {
	if m <= 2 {
		y--
	}
	era := FloorDiv(y, 400)
	yoe := y - era*400
	mp := int64((m + 9) % 12)
	doy := (153*mp+2)/5 + int64(d) - 1
	doe := yoe*365 + yoe/4 - yoe/100 + doy
	return era*146097 + doe - 719468
}

// CivilFromDays is the inverse of DaysFromCivil.
func CivilFromDays(z int64) (y int64, m, d int) {
	z += 719468
	era := FloorDiv(z, 146097)
	doe := z - era*146097
	yoe := (doe - doe/1460 + doe/36524 - doe/146096) / 365
	y = yoe + era*400
	doy := doe - (365*yoe + yoe/4 - yoe/100)
	mp := (5*doy + 2) / 153
	d = int(doy - (153*mp+2)/5 + 1)
	if mp < 10 {
		m = int(mp + 3)
	} else {
		m = int(mp - 9)
	}
	if m <= 2 {
		y++
	}
	return y, m, d
}

// IsLeap reports whether y is a Gregorian leap year.
func IsLeap(y int64) bool {
	return y%4 == 0 && (y%100 != 0 || y%400 == 0)
}

var monthDays = [13]int{0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31}

// DaysInMonth returns the length of month m (1-12) in year y.
func DaysInMonth(y int64, m int) int {
	if m == 2 && IsLeap(y) {
		return 29
	}
	return monthDays[m]
}

// Weekday returns the day of the week (0 = Sunday) of a Unix day number.
func Weekday(days int64) int {
	w := (days + 4) % 7 // 1970-01-01 was a Thursday
	if w < 0 {
		w += 7
	}
	return int(w)
}
