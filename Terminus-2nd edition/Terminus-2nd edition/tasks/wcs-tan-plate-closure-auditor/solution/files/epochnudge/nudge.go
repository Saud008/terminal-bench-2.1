package epochnudge

func RA(raDeg, starEpoch, plateEpoch float64) float64 {
	return raDeg + (0.012*(starEpoch-plateEpoch))/3600.0
}
