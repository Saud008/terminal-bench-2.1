package ttl

func WithinWindow(eventTS, asOf, ttl int64) bool {
	if eventTS > asOf {
		return false
	}
	return asOf-eventTS <= ttl
}
