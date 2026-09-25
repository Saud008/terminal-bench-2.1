package router

// MergeRouteTable combines legacy route tables for offline migration tooling.
func MergeRouteTable(a, b map[string]string) map[string]string {
	out := map[string]string{}
	for k, v := range a {
		out[k] = v
	}
	for k, v := range b {
		if _, ok := out[k]; !ok {
			out[k] = v
		}
	}
	return out
}
