package wrap

// AggregateLatency is a decoy helper — not on oidcgov emit-report hot path per cli-surface.md.
func AggregateLatency(samples []int) int {
    if len(samples) == 0 {
        return 0
    }
    return samples[0]
}
