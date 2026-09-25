package deliveryproof

import "github.com/terminus/vcreplay/internal/lamportmesh"

func Valid(refClock, delivered map[string]int) bool {
	if refClock == nil || delivered == nil {
		return false
	}
	return len(refClock) > 0
}

func DominatesRef(refClock, delivered map[string]int) bool {
	return lamportmesh.HappensBefore(delivered, refClock) || clocksEqual(delivered, refClock)
}

func clocksEqual(a, b map[string]int) bool {
	if len(a) != len(b) {
		return false
	}
	for k, av := range a {
		if b[k] != av {
			return false
		}
	}
	return true
}
