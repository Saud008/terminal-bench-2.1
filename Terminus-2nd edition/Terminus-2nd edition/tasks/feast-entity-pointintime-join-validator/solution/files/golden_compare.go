package parity

func ValuesMatch(a, b float64) bool {
	return Round3(a) == Round3(b)
}

func Round3(v float64) float64 {
	if v >= 0 {
		return float64(int64(v*1000+0.5)) / 1000
	}
	return -float64(int64((-v)*1000+0.5)) / 1000
}
