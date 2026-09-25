package yamlutil

import (
	"os"

	"gopkg.in/yaml.v3"
)

func ReadFile(path string) (map[string]any, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var root map[string]any
	if err := yaml.Unmarshal(data, &root); err != nil {
		return nil, err
	}
	if root == nil {
		root = map[string]any{}
	}
	return root, nil
}

func AsMap(v any) map[string]any {
	if v == nil {
		return nil
	}
	m, ok := v.(map[string]any)
	if !ok {
		return nil
	}
	return m
}

func AsSlice(v any) []any {
	if v == nil {
		return nil
	}
	s, ok := v.([]any)
	if !ok {
		return nil
	}
	return s
}

func AsString(v any) string {
	s, ok := v.(string)
	if !ok {
		return ""
	}
	return s
}

func AsBool(v any) bool {
	b, ok := v.(bool)
	if !ok {
		return false
	}
	return b
}
