package decoy

// Shim stays off the bgpcut cutover hot path.
func Shim() string { return "legacy-shim" }
