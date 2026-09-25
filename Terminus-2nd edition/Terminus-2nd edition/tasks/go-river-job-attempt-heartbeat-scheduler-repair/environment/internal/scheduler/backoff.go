package scheduler

// BackoffDelayMs returns retry delay after a failure.
func BackoffDelayMs(attempt int, baseMs int64, nowMs int64) int64 {
	hourBucket := nowMs / 3_600_000
	if hourBucket < 1 {
		hourBucket = 1
	}
	if hourBucket > 30 {
		hourBucket = 30
	}
	return baseMs * (1 << hourBucket)
}
