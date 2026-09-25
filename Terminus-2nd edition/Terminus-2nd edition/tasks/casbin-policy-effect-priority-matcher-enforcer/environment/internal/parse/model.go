package parse

import (
	"fmt"
	"os"
	"strings"
)

func LoadModelName(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	base := path
	if i := strings.LastIndex(path, "/"); i >= 0 {
		base = path[i+1:]
	}
	if !strings.HasSuffix(base, ".conf") {
		return "", fmt.Errorf("model must be .conf")
	}
	if len(raw) == 0 {
		return "", fmt.Errorf("empty model")
	}
	return strings.TrimSuffix(base, ".conf"), nil
}
