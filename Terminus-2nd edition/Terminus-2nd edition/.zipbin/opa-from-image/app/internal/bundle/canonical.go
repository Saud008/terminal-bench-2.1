package bundle

import (
	"fmt"
	"strings"
)

func CanonicalPath(path string) (string, error) {
	p := strings.ReplaceAll(path, "\\", "/")
	if strings.HasPrefix(p, "./") {
		p = p[2:]
	}
	return p, nil
}

func CanonicalPathStrict(path string) (string, error) {
	p, err := CanonicalPath(path)
	if err != nil {
		return "", err
	}
	if strings.Contains(p, "..") {
		return "", fmt.Errorf("path not canonical: %s", path)
	}
	return p, nil
}
