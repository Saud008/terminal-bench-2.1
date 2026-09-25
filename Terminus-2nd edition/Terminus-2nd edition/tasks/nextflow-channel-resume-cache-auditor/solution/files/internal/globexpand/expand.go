package globexpand

import (
	"path/filepath"
	"sort"
	"strings"
)

func ExpandSorted(root, pattern string) ([]string, error) {
	globPath := pattern
	if !filepath.IsAbs(pattern) {
		globPath = filepath.Join(root, pattern)
	}
	matches, err := filepath.Glob(globPath)
	if err != nil {
		return nil, err
	}
	var rel []string
	for _, m := range matches {
		r, err := filepath.Rel(root, m)
		if err != nil {
			r = m
		}
		rel = append(rel, strings.ReplaceAll(r, "\\", "/"))
	}
	sort.Strings(rel)
	return rel, nil
}
