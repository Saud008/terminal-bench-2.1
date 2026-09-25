package manifestload

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/terminus/pqgov/internal/model"
)

func LoadManifests(tenantID, scenario, fixtureDir string) ([]model.OperationManifest, error) {
	root := filepath.Join(fixtureDir, "tenants", scenario, "manifests")
	entries, err := os.ReadDir(root)
	if err != nil {
		return nil, err
	}
	var names []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".json") {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)
	out := make([]model.OperationManifest, 0, len(names))
	for _, name := range names {
		raw, err := os.ReadFile(filepath.Join(root, name))
		if err != nil {
			return nil, err
		}
		var m model.OperationManifest
		if err := json.Unmarshal(raw, &m); err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, nil
}

func NormalizeQuery(query string) string {
	parts := strings.Fields(strings.TrimSpace(query))
	return strings.Join(parts, " ")
}

func ComputeOperationHash(query string) string {
	norm := NormalizeQuery(query)
	sum := sha256.Sum256([]byte(norm))
	return hex.EncodeToString(sum[:])
}

func ValidateManifestHashes(m model.OperationManifest) error {
	computed := ComputeOperationHash(m.QueryText)
	if computed != m.OperationHash {
		return fmt.Errorf("operation hash mismatch for %s", m.OperationID)
	}
	return nil
}

func ToStaged(m model.OperationManifest) model.StagedOperation {
	return model.StagedOperation{
		OperationID:    m.OperationID,
		OperationHash:  m.OperationHash,
		SchemaHash:     m.SchemaHash,
		RegisteredAtMs: m.RegisteredAtMs,
		LastSeenMs:     m.LastSeenMs,
	}
}
