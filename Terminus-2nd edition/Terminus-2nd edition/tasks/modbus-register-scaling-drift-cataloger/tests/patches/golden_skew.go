package clock

import "math"

func IsStale(receivedMs, deviceClockMs, skewLimit int64) bool {
	if skewLimit <= 0 {
		return false
	}
	return int64(math.Abs(float64(deviceClockMs-receivedMs))) > skewLimit
}
