package decoy

// DecorativeJoinRank is not used by load, validate, or export.
func DecorativeJoinRank(a, b int64) int64 {
	if a > b {
		return a
	}
	return b
}
