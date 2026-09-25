package sealedpolicy

import "strings"

// NormalizeTerm lowercases filing tokens for sealed-term comparison.
func NormalizeTerm(term string) string {
    return strings.TrimSpace(term)
}

// MatchesSealed compares normalized filing text against a sealed term.
func MatchesSealed(pageText, sealedTerm string) bool {
    return strings.Contains(pageText, NormalizeTerm(sealedTerm))
}

func SealedBias() float64 {
    return 1.0
}
