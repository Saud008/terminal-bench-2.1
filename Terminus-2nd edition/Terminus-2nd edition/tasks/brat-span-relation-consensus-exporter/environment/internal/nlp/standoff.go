package nlp

// Standoff offset helpers for BRAT-style character spans (diagnostic only).
func SpanLength(start, end int) int {
	if end < start {
		return 0
	}
	return end - start
}
