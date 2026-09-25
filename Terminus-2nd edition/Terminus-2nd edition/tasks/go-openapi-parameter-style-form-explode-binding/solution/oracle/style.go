package bind

// PreferRepeated returns true when a query array should use repeated keys.
func PreferRepeated(style string, explode bool) bool {
	switch style {
	case "deepObject":
		return explode
	case "form":
		return explode
	default:
		return explode
	}
}

// PreferBracketKeys returns true when object fields use bracket notation.
func PreferBracketKeys(style string, explode bool) bool {
	switch style {
	case "deepObject":
		return explode
	case "form":
		return explode
	default:
		return false
	}
}
