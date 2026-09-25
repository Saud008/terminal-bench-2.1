package rrule

import "time"

func limitCount(items []time.Time, count int) []time.Time {
	if count <= 0 {
		return items
	}
	if len(items) > count {
		return items[:count]
	}
	return items
}
