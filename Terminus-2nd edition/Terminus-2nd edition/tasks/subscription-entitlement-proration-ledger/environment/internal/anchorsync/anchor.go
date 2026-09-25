package anchorsync

type Shift struct {
	EffectiveDate string
	NewAnchorDay  int
}

func AdjustWindowEnd(windowStart, windowEnd, cycleEnd string, shifts []Shift) string {
	return windowEnd
}
