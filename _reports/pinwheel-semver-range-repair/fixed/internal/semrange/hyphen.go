package semrange

// hyphen expands "from - to". A partial on the left fills missing fields with
// zeros; a partial on the right covers every version it matches.
func hyphen(from, to partial) []Comparator {
	var set []Comparator
	if from.fields > 0 {
		set = append(set, Comparator{Op: OpGTE, Version: from.version()})
	}
	switch {
	case to.fields == 3:
		set = append(set, Comparator{Op: OpLTE, Version: to.version()})
	case to.fields > 0:
		set = append(set, Comparator{Op: OpLT, Version: to.next().Floor()})
	}
	if len(set) == 0 {
		set = append(set, matchAll)
	}
	return set
}
