package filter

import "strings"

// MatchFilter reports whether subject matches a JetStream FilterSubject pattern.
func MatchFilter(subject, pattern string) bool {
	if pattern == "" || pattern == ">" {
		return true
	}
	subjTokens := strings.Split(subject, ".")
	patTokens := strings.Split(pattern, ".")
	if len(subjTokens) != len(patTokens) {
		return false
	}
	for i := range subjTokens {
		if patTokens[i] == "*" {
			continue
		}
		if patTokens[i] != subjTokens[i] {
			return false
		}
	}
	return true
}
