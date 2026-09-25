package zoninghold

// ActiveHoldRank returns the winning hold rank for a district (higher rank wins).
func ActiveHoldRank(holdRank int, active bool) int {
	if !active {
		return 0
	}
	return holdRank
}

func BlocksPermit(permitHoldRank, districtHoldRank int) bool {
	if districtHoldRank == 0 {
		return false
	}
	return permitHoldRank < districtHoldRank
}
