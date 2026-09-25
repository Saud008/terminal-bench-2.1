package version

import "strings"

func GateOpen(handlerVersion, minVersion string) bool {
	return strings.Compare(handlerVersion, minVersion) >= 0
}
