package credmatch

func CertOK(inspectorLevel, required int) bool {
	return inspectorLevel > required
}

func CapOK(currentLoad int, maxCap int) bool {
	return currentLoad < maxCap
}
