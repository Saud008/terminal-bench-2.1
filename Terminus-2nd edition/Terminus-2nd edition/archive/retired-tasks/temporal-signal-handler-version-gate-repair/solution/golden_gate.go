package version

import (
	"strconv"
	"strings"
)

func parseTuple(v string) [3]int {
	parts := strings.Split(v, ".")
	out := [3]int{}
	for i := 0; i < 3 && i < len(parts); i++ {
		n, _ := strconv.Atoi(parts[i])
		out[i] = n
	}
	return out
}

func GateOpen(handlerVersion, minVersion string) bool {
	h := parseTuple(handlerVersion)
	m := parseTuple(minVersion)
	for i := 0; i < 3; i++ {
		if h[i] > m[i] {
			return true
		}
		if h[i] < m[i] {
			return false
		}
	}
	return true
}
