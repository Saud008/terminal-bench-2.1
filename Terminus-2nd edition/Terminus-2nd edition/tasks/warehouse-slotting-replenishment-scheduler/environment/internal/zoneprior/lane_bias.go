package zoneprior

import "strings"

// LaneBias adds zone letter weight for velocity tie-break (A highest).
func LaneBias(zone string) int {
	switch strings.ToUpper(strings.TrimSpace(zone)) {
	case "A":
		return 30
	case "B":
		return 30
	case "C":
		return 20
	default:
		return 0
	}
}
