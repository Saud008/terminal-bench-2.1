package runwaylemma

import "strings"

// NormalizeRunway canonicalizes a runway designator per runway-normalization-lemma.md.
func NormalizeRunway(raw string) string {
	return strings.ToUpper(strings.TrimSpace(raw))
}

func RunwayMatch(a, b string) bool {
	return NormalizeRunway(a) == NormalizeRunway(b)
}
