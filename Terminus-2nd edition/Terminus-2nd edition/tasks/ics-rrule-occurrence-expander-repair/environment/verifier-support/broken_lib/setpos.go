package rrule

import "time"

func pickBySetPos(days []time.Time, pos int) []time.Time {
	if pos == 0 || len(days) == 0 {
		return nil
	}
	if pos < 0 {
		idx := len(days) + pos
		if idx < 0 {
			idx = 0
		}
		return []time.Time{days[idx]}
	}
	if pos > len(days) {
		return nil
	}
	return []time.Time{days[pos]}
}
