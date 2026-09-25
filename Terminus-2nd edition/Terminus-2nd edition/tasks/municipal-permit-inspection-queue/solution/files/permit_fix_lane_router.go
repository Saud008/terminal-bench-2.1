package laneassign

import "strings"

func RouteLane(permitType string, routes map[string]string) string {
	if lane, ok := routes[permitType]; ok {
		return lane
	}
	if strings.HasPrefix(permitType, "electrical") {
		return "lane-electrical"
	}
	return "lane-general"
}

func MinCertForLane(lane string, floors map[string]int) int {
	if v, ok := floors[lane]; ok {
		return v
	}
	return 1
}
