package revoke

// DocumentActive reports whether a travel document may be used.
func DocumentActive(docRevoked bool, passportRevoked bool, isVisa bool) bool {
	if docRevoked {
		return false
	}
	if !isVisa && passportRevoked {
		return false
	}
	return true
}
