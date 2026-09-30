// Package manifest reads a project's pin.json.
package manifest

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	"github.com/brightloom/pinwheel/internal/semrange"
)

// FileName is the manifest's name inside a project directory.
const FileName = "pin.json"

// Manifest is a parsed pin.json.
type Manifest struct {
	Name         string            `json:"name"`
	Dependencies map[string]string `json:"dependencies"`
	Overrides    map[string]string `json:"overrides"`
	Prefer       string            `json:"prefer"`
}

// Load reads and validates a manifest.
func Load(path string) (*Manifest, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("manifest: %w", err)
	}
	var m Manifest
	dec := json.NewDecoder(bytes.NewReader(data))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&m); err != nil {
		return nil, fmt.Errorf("manifest: %w", err)
	}
	if m.Name == "" {
		return nil, fmt.Errorf("manifest: missing name")
	}
	switch m.Prefer {
	case "", "highest", "lowest":
	default:
		return nil, fmt.Errorf("manifest: prefer must be \"highest\" or \"lowest\", got %q", m.Prefer)
	}
	for _, field := range []struct {
		label  string
		ranges map[string]string
	}{{"dependencies", m.Dependencies}, {"overrides", m.Overrides}} {
		for name, r := range field.ranges {
			if _, err := semrange.Parse(r); err != nil {
				return nil, fmt.Errorf("manifest: %s.%s: %w", field.label, name, err)
			}
		}
	}
	return &m, nil
}

// PreferLowest reports whether the project asks for the lowest eligible releases.
func (m *Manifest) PreferLowest() bool { return m.Prefer == "lowest" }
