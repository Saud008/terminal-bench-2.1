package merge

// ApplyChildMerge is a legacy merge helper (not on export hot path).
func ApplyChildMerge(a, b []string) []string {
	out := append([]string(nil), a...)
	for _, x := range b {
		found := false
		for _, y := range out {
			if y == x {
				found = true
				break
			}
		}
		if !found {
			out = append(out, x)
		}
	}
	return out
}
