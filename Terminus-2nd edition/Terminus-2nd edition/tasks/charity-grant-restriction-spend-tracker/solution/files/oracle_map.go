package codealias

func NormalizeProject(input string, aliases map[string]string) string {
	if out, ok := aliases[input]; ok && out != "" {
		return out
	}
	return input
}
