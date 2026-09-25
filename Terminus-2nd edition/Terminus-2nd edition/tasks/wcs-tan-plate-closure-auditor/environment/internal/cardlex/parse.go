package cardlex

import "strings"

// Parse maps trimmed keywords to trimmed values.
func Parse(cards []string) map[string]string {
	out := map[string]string{}
	for _, card := range cards {
		parts := strings.SplitN(card, "=", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		val := strings.TrimSpace(parts[1])
		out[key] = val
	}
	return out
}
