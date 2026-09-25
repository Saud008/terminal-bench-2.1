package normalize

import "strings"

func CanonicalID(identifier string) string {
	id := strings.TrimSpace(identifier)
	if len(id) >= 2 && id[0] == '"' && id[len(id)-1] == '"' {
		id = id[1 : len(id)-1]
	}
	return strings.ReplaceAll(id, `\/`, `/`)
}
