package bundle

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type Manifest struct {
	Revision string   `json:"revision"`
	Roots    []string `json:"roots"`
	Members  []string `json:"members"`
}

func LoadManifest(bundleDir string) (*Manifest, error) {
	raw, err := os.ReadFile(filepath.Join(bundleDir, "MANIFEST.json"))
	if err != nil {
		return nil, err
	}
	var m Manifest
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	return &m, nil
}

func ChainMembers(m *Manifest) []string {
	out := make([]string, 0, len(m.Members))
	for _, p := range m.Members {
		if p == "MANIFEST.json" || p == ".signatures.json" {
			continue
		}
		out = append(out, p)
	}
	return out
}
