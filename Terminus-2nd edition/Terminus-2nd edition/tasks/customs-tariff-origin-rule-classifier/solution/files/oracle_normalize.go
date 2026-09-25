package codify

import "strings"

func NormalizeHS(raw string) string {
	cleaned := strings.NewReplacer(".", "", "-", "", " ", "").Replace(raw)
	if len(cleaned) > 10 {
		cleaned = cleaned[:10]
	}
	for len(cleaned) < 10 {
		cleaned = cleaned + "0"
	}
	return cleaned
}
