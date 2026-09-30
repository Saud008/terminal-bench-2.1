package semrange

// hyphen expands "from - to", an inclusive range. Missing fields on either
// end are filled with zeros.
func hyphen(from, to partial) []Comparator {
	var set []Comparator
	if from.fields > 0 {
		set = append(set, Comparator{Op: OpGTE, Version: from.version()})
	}
	if to.fields > 0 {
		set = append(set, Comparator{Op: OpLTE, Version: to.version()})
	}
	if len(set) == 0 {
		set = append(set, matchAll)
	}
	return set
}
