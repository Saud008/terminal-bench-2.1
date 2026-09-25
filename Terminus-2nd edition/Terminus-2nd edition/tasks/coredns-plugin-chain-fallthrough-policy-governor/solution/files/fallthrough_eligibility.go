package chain

func AllowsFallthrough(zone, qname string, enabled bool) bool {
	if !enabled {
		return false
	}
	return true
}
