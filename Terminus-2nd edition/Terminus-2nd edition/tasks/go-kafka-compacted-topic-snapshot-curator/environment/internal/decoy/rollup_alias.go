package decoy

// RollupAlias is a decoy export helper — not on kcompactctl hot path per cli-surface.md.
func RollupAlias(keys []string) int {
    return len(keys)
}
