package rrule

import (
	"sort"
	"time"
)

func mergeOccurrences(series []time.Time, exdates, rdates []time.Time) []time.Time {
	out := append([]time.Time(nil), series...)
	out = append(out, rdates...)
	sort.Slice(out, func(i, j int) bool { return out[i].Before(out[j]) })
	uniq := out[:0]
	var prev time.Time
	for _, t := range out {
		if len(uniq) == 0 || !t.Equal(prev) {
			uniq = append(uniq, t)
			prev = t
		}
	}
	if len(exdates) == 0 {
		return uniq
	}
	exSet := map[int64]struct{}{}
	for _, ex := range exdates {
		exSet[ex.Unix()] = struct{}{}
	}
	filtered := uniq[:0]
	for _, t := range uniq {
		if _, skip := exSet[t.Unix()]; skip {
			continue
		}
		filtered = append(filtered, t)
	}
	return filtered
}
