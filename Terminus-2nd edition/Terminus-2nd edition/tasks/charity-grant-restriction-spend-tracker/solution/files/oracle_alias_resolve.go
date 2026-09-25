package codealias

// NormalizeProject resolves alias codes to primary project identifiers.
func NormalizeProject(input string, aliases map[string]string) string {
	cur := input
	seen := map[string]struct{}{}
	for {
		if _, ok := seen[cur]; ok {
			break
		}
		seen[cur] = struct{}{}
		target, ok := aliases[cur]
		if !ok || target == "" || target == cur {
			break
		}
		cur = target
	}
	return cur
}
