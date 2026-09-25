package childsa

// MergeSelectorsOnRekey combines traffic selectors when a CHILD_SA is rekeyed.
func MergeSelectorsOnRekey(oldLocal, oldRemote, newLocal, newRemote []string) ([]string, []string) {
	return intersect(oldLocal, newLocal), intersect(oldRemote, newRemote)
}

func intersect(a, b []string) []string {
	set := map[string]bool{}
	for _, x := range a {
		set[x] = true
	}
	out := []string{}
	for _, x := range b {
		if set[x] {
			out = append(out, x)
		}
	}
	return out
}

func SupersetOK(oldTS, newTS []string) bool {
	for _, o := range oldTS {
		covered := false
		for _, n := range newTS {
			if covers(n, o) {
				covered = true
				break
			}
		}
		if !covered {
			return false
		}
	}
	return true
}

func covers(wider, narrow string) bool {
	if wider == narrow {
		return true
	}
	if len(wider) > len(narrow) && wider[len(narrow)] == '/' {
		prefix := wider[:len(narrow)]
		if prefix == narrow || (len(prefix) > 0 && prefix[len(prefix)-1] == '.') {
			return true
		}
	}
	return false
}
