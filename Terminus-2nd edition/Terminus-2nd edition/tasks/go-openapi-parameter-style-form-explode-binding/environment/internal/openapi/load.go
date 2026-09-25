package openapi

import (
	"os"

	"gopkg.in/yaml.v3"
)

func LoadFile(path string) (Document, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return Document{}, err
	}
	var doc Document
	if err := yaml.Unmarshal(raw, &doc); err != nil {
		return Document{}, err
	}
	return doc, nil
}
