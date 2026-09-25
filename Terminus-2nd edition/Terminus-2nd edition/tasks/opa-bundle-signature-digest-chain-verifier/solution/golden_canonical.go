package bundle

import (
	"fmt"
	"strings"
)

func CanonicalPath(path string) (string, error) {
	p := strings.ReplaceAll(path, "\\", "/")
	p = strings.TrimPrefix(p, "./")
	parts := make([]string, 0)
	for _, part := range strings.Split(p, "/") {
		if part == "" || part == "." {
			continue
		}
		if part == ".." {
			if len(parts) == 0 {
				return "", fmt.Errorf("path escapes bundle root: %s", path)
			}
			parts = parts[:len(parts)-1]
			continue
		}
		parts = append(parts, part)
	}
	return strings.Join(parts, "/"), nil
}
