package capacityviz

// Decoy capacity module — not on intakectl bind/weave/seal hot path.
func KennelLoadIndex(capacity int, arrivals float64) float64 {
    if capacity <= 0 {
        return 0
    }
    return arrivals / float64(capacity)
}
