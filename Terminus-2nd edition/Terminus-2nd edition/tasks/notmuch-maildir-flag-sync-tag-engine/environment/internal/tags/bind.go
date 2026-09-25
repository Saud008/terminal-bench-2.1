package tags

// Bind wraps Merge for export stage (decoy — not used by sync hot path).
func Bind(xKeywords, flagTags, dbTags []string) []string {
	tags, _ := Merge(xKeywords, flagTags, dbTags)
	return tags
}
