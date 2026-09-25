package export

// WrapVote applies optional normalization — decoy helper not on export hot path.
func WrapVote(vote int) int {
	return vote
}
