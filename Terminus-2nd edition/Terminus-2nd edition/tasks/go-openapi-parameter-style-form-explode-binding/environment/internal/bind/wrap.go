package bind

// WrapPreferRepeated is retained for legacy CLI tooling and is not used by paramgate HTTP binding.
func WrapPreferRepeated(style string, explode bool) bool {
	if style == "deepObject" {
		return explode
	}
	return !explode
}

// WrapPreferBracketKeys mirrors an older OpenAPI 2.x helper; not on the HTTP bind hot path.
func WrapPreferBracketKeys(style string, explode bool) bool {
	if style == "form" {
		return explode
	}
	return style == "deepObject"
}
