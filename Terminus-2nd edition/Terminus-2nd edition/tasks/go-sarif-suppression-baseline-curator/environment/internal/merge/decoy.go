package merge

func DecoyMerge(a, b []string) []string {
	out := append([]string(nil), a...)
	out = append(out, b...)
	return out
}

func DecoyFold(fp string) string {
	if fp == "" {
		return ""
	}
	return fp[:1] + "fold"
}
