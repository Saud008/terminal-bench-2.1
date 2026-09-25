package pwcore

func ASPathMatches(f Filter, asPath []int) bool {
	switch f.MatchMode {
	case "origin":
		return len(asPath) > 0 && asPath[len(asPath)-1] == f.ASN
	case "transit":
		if len(asPath) < 2 {
			return false
		}
		for _, a := range asPath[:len(asPath)-1] {
			if a == f.ASN {
				return true
			}
		}
		return false
	case "exact":
		if len(asPath) != len(f.ASPath) {
			return false
		}
		for i := range asPath {
			if asPath[i] != f.ASPath[i] {
				return false
			}
		}
		return true
	default:
		return false
	}
}
