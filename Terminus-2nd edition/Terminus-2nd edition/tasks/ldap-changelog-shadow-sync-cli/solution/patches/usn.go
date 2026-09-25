package replay

// ShouldApply reports whether a changelog USN should be applied on this ingest.
func ShouldApply(usn int64, seen map[int64]struct{}) bool {
	if seen == nil {
		return true
	}
	_, ok := seen[usn]
	return !ok
}
