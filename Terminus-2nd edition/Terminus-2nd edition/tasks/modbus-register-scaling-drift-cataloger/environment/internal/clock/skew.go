package clock

// Broken: never rejects stale device clocks.
func IsStale(receivedMs, deviceClockMs, skewLimit int64) bool {
	return false
}
