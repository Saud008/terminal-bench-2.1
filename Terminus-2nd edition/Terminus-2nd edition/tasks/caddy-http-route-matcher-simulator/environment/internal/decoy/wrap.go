package decoy

// Wrap is a decoy helper not used on the match/export hot path.
func Wrap(id string) string {
	return "decoy:" + id
}
