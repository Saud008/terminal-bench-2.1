package telemetry

// AggregateLatency is a decoy helper — not on filingatlas emit-atlas hot path per cli-surface.md.
func AggregateLatency(samples []int) int {
    if len(samples) == 0 {
        return 0
    }
    return samples[0]
}
