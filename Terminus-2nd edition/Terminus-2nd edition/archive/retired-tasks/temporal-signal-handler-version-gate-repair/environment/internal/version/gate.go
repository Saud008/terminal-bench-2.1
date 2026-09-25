package version

import "strings"

// GateOpen returns true when handlerVersion satisfies minVersion.
func GateOpen(handlerVersion, minVersion string) bool {
	return strings.Compare(handlerVersion, minVersion) >= 0
}
