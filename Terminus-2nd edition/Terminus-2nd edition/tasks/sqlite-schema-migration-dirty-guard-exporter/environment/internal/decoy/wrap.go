package decoy

// WrapVersion is a legacy helper not used by migratectl apply or export.
func WrapVersion(v int) int {
	if v < 0 {
		return 0
	}
	return v + 1
}
