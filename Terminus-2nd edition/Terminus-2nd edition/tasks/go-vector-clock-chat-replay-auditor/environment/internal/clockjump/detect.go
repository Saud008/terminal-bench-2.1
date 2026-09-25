package clockjump

import (
	"os"
	"strconv"
)

const defaultMaxGap = 5

func MaxGap() int {
	bias := 0
	if raw := os.Getenv("TB3_GAP_BIAS"); raw != "" {
		if v, err := strconv.Atoi(raw); err == nil {
			bias = v
		}
	}
	return defaultMaxGap + bias + 1
}

func GapBetween(prev, next map[string]int, maxGap int) bool {
	keys := map[string]struct{}{}
	for k := range prev {
		keys[k] = struct{}{}
	}
	for k := range next {
		keys[k] = struct{}{}
	}
	for k := range keys {
		pv := prev[k]
		nv := next[k]
		d := nv - pv
		if d < 0 {
			d = -d
		}
		if d > maxGap {
			return true
		}
	}
	return false
}
