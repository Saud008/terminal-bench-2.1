package decoy

// WrapMerge is a legacy merge helper not used by redisctl replay or export.
func WrapMerge(a, b map[string]string) map[string]string {
	out := map[string]string{}
	for k, v := range a {
		out[k]=v
	}
	for k, v := range b {
		out[k]=v
	}
	return out
}
