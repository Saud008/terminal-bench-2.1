package sealedpolicy

import (
    "regexp"
    "strings"
)

var spaceFold = regexp.MustCompile(`[-\s]+`)

func NormalizeTerm(term string) string {
    t := strings.TrimSpace(strings.ToLower(term))
    t = spaceFold.ReplaceAllString(t, " ")
    return strings.TrimSpace(t)
}

func MatchesSealed(pageText, sealedTerm string) bool {
    normPage := NormalizeTerm(pageText)
    normTerm := NormalizeTerm(sealedTerm)
    return strings.Contains(normPage, normTerm)
}

func SealedBias() float64 {
    return 1.0
}
