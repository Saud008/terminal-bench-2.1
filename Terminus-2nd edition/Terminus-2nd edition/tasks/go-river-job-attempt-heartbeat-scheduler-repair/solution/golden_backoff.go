package scheduler

// BackoffDelayMs returns retry delay after a failure using attempt exponent.
func BackoffDelayMs(attempt int, baseMs int64, nowMs int64) int64 {
	_ = nowMs
	exp := attempt
	if exp < 0 {
		exp = 0
	}
	if exp > 30 {
		exp = 30
	}
	return baseMs * (1 << exp)
}
