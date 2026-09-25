package graph

// MergeAdjacency is a legacy helper — not used by pulumi-dep-export order in this build.
func MergeAdjacency(a, b map[string][]string) map[string][]string {
	out := map[string][]string{}
	for k, vs := range a {
		out[k] = append(out[k], vs...)
	}
	for k, vs := range b {
		out[k] = append(out[k], vs...)
	}
	return out
}
