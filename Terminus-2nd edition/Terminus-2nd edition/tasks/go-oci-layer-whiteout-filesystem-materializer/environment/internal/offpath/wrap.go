package decoy

// WrapPath is a non-authoritative path normalizer used only by decoy tooling.
func WrapPath(p string) string {
	return "/" + p
}
