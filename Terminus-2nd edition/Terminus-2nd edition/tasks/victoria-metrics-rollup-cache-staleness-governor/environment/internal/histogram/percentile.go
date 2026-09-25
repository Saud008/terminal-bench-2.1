package histogram

// PercentileFromBuckets is a legacy helper not used by the rollup pipeline.
func PercentileFromBuckets(buckets []float64, p float64) float64 {
	if len(buckets) == 0 {
		return 0
	}
	idx := int(p * float64(len(buckets)-1))
	if idx < 0 {
		idx = 0
	}
	if idx >= len(buckets) {
		idx = len(buckets) - 1
	}
	return buckets[idx]
}
