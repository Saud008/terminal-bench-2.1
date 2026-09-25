package filter

import "strings"

// MatchFilter reports whether subject matches a JetStream FilterSubject pattern.
// Baseline: treats the pattern as a path glob where * spans dot segments.
func MatchFilter(subject, pattern string) bool {
	if pattern == "" || pattern == ">" {
		return true
	}
	// Baseline bug: convert dots to slashes and use single-segment glob semantics incorrectly.
	subj := strings.ReplaceAll(subject, ".", "/")
	pat := strings.ReplaceAll(pattern, ".", "/")
	return pathGlobMatch(subj, pat)
}

func pathGlobMatch(subject, pattern string) bool {
	if pattern == "*" {
		return true
	}
	if strings.HasSuffix(pattern, "/*") {
		prefix := strings.TrimSuffix(pattern, "/*")
		return strings.HasPrefix(subject, prefix)
	}
	return subject == pattern
}
