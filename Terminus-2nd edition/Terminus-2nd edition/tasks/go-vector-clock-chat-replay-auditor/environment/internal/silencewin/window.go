package silencewin

func Active(ts, startMs, endMs int64) bool {
	return ts >= startMs && ts <= endMs
}
