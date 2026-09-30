package ini

// isCommentAt reports whether s[i] opens an inline comment.
func isCommentAt(s string, i int) bool {
	return s[i] == ';' || s[i] == '#'
}

// indexOrComment returns the index of the first c in s, or of the first
// inline comment if that comes earlier, or len(s).
func indexOrComment(s string, c byte) int {
	for i := 0; i < len(s); i++ {
		if s[i] == c || isCommentAt(s, i) {
			return i
		}
	}
	return len(s)
}

// lastIndexBeforeComment returns the index of the last c in s before any
// inline comment, or 0 when there is none (the caller checks s[0]).
func lastIndexBeforeComment(s string, c byte) int {
	last := 0
	for i := 0; i < len(s) && !isCommentAt(s, i); i++ {
		if s[i] == c {
			last = i
		}
	}
	return last
}

// stripComment cuts an inline comment off a value.
func stripComment(value string) string {
	for i := 0; i < len(value); i++ {
		if isCommentAt(value, i) {
			return value[:i]
		}
	}
	return value
}
