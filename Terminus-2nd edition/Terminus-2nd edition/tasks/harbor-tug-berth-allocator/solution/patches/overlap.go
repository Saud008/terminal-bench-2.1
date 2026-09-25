package overlap

import (
	"time"

	"github.com/harbor/tug-berth/internal/db"
)

func ConcurrentOverlapMinutes(assignments []db.Assignment) map[string]int {
	byBerth := map[string][]db.Assignment{}
	for _, a := range assignments {
		byBerth[a.BerthID] = append(byBerth[a.BerthID], a)
	}
	out := map[string]int{}
	for berth, list := range byBerth {
		out[berth] = pairwiseOverlap(list)
	}
	return out
}

func pairwiseOverlap(list []db.Assignment) int {
	total := 0
	for i := 0; i < len(list); i++ {
		for j := i + 1; j < len(list); j++ {
			total += intersectMinutes(list[i], list[j])
		}
	}
	return total
}

func intersectMinutes(a, b db.Assignment) int {
	s1, e1 := parse(a.ArrivalUTC, a.DepartureUTC)
	s2, e2 := parse(b.ArrivalUTC, b.DepartureUTC)
	start := maxTime(s1, s2)
	end := minTime(e1, e2)
	if !end.After(start) {
		return 0
	}
	return int(end.Sub(start).Minutes())
}

func parse(arrival, departure string) (time.Time, time.Time) {
	s, _ := time.Parse(time.RFC3339, arrival)
	e, _ := time.Parse(time.RFC3339, departure)
	return s, e
}

func maxTime(a, b time.Time) time.Time {
	if a.After(b) {
		return a
	}
	return b
}

func minTime(a, b time.Time) time.Time {
	if a.Before(b) {
		return a
	}
	return b
}

func MaxDwellPerBerth(assignments []db.Assignment) map[string]int {
	out := map[string]int{}
	for _, a := range assignments {
		d := int(parseEnd(a).Sub(parseStart(a)).Minutes())
		if d > out[a.BerthID] {
			out[a.BerthID] = d
		}
	}
	return out
}

func parseStart(a db.Assignment) time.Time {
	t, _ := time.Parse(time.RFC3339, a.ArrivalUTC)
	return t
}

func parseEnd(a db.Assignment) time.Time {
	t, _ := time.Parse(time.RFC3339, a.DepartureUTC)
	return t
}

func TotalDwellMinutes(assignments []db.Assignment) map[string]int {
	out := map[string]int{}
	for _, a := range assignments {
		d := int(parseEnd(a).Sub(parseStart(a)).Minutes())
		out[a.BerthID] += d
	}
	return out
}
