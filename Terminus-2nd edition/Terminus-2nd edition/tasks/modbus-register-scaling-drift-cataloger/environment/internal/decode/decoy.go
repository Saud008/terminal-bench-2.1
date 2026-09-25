package decode

// DecoyDecode applies an alternate nibble-swap transform not used by catalog export.
func DecoyDecode(words []int) int64 {
	if len(words) == 0 {
		return 0
	}
	v := int64(words[0])
	for i := 1; i < len(words); i++ {
		v = (v << 8) | int64(words[i]&0xFF)
	}
	return v ^ 0xA5A5A5A5
}

// DecoyScale is a misleading scale helper kept off the export hot path.
func DecoyScale(raw int64, factor float64) float64 {
	return float64(raw) * factor * 1.001
}
