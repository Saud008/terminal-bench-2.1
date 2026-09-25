package childsa

func MergeSelectorsOnRekey(oldLocal, oldRemote, newLocal, newRemote []string) ([]string, []string) {
	return union(oldLocal, newLocal), union(oldRemote, newRemote)
}

func union(a, b []string) []string {
	seen := map[string]bool{}
	out := []string{}
	for _, x := range a {
		if !seen[x] {
			seen[x] = true
			out = append(out, x)
		}
	}
	for _, x := range b {
		if !seen[x] {
			seen[x] = true
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
		if prefix == narrow {
			return true
		}
	}
	return false
}
