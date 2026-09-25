package parse

import "strings"

func TypeName(identifier string) string {
	parts := strings.Split(identifier, "/")
	if len(parts) < 3 {
		return ""
	}
	base := parts[1]
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
	if len(names) > count {
		return names[:count]
	}
	for len(names) < count {
		names = append(names, "unknown")
	}
	return names
}
