package decoy

// WrapSubjects is a legacy helper not used by natsctl replay or export.
func WrapSubjects(subjects []string, prefix string) []string {
	out := make([]string, len(subjects))
	for i, s := range subjects {
		out[i] = prefix + s
	}
	return out
}
