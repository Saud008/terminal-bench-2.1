package revparviz

// Decoy revpar module — not on overbookctl publish hot path.
func RevParIndex(nights int, peakRate float64) float64 {
    if nights <= 0 {
        return 0
    }
    return peakRate * float64(nights)
}
