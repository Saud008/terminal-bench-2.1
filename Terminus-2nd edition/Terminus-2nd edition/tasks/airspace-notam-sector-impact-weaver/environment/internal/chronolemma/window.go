package chronolemma

// ActiveAt reports whether evalMinute falls inside the activation window
// [startMinute, endMinute] per chronology-window-lemma.md.
func ActiveAt(startMinute, endMinute, evalMinute int) bool {
	if endMinute < startMinute {
		return false
	}
	return evalMinute >= startMinute && evalMinute <= endMinute
}
