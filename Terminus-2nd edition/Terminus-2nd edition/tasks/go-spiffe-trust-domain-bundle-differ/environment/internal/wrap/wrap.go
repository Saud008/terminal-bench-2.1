package wrap

// CombineTrustDomains is a decoy helper — not on spiffectl publish hot path per cli-surface.md.
func CombineTrustDomains(domains []string) int {
    return len(domains)
}
