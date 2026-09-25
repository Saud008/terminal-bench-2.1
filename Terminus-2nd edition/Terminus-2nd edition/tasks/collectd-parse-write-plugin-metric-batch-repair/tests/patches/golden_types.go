package parse

import (
	"sort"
	"strings"
)

func TypeName(identifier string) string {
	parts := strings.Split(identifier, "/")
	if len(parts) < 3 {
		return ""
	}
	base := parts[2]
	if idx := strings.Index(base, "-"); idx >= 0 {
		base = base[:idx]
	}
	return base
}

func DSNames(typeName string, count int, typesDB map[string]map[string]string) []string {
	dsMap := typesDB[typeName]
	if dsMap == nil {
		return nil
	}
	names := make([]string, 0, len(dsMap))
	for name := range dsMap {
		names = append(names, name)
	}
	sort.Strings(names)
	if len(names) > count {
		return names[:count]
	}
	for len(names) < count {
		names = append(names, "unknown")
	}
	return names
}
