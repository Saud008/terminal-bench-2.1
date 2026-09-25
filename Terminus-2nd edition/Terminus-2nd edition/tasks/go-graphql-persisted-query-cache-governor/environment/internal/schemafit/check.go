package schemafit

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/pqgov/internal/model"
)

type schemaCatalog struct {
	Tenants map[string]tenantSchema `json:"tenants"`
}

type tenantSchema struct {
	SchemaHash string `json:"schema_hash"`
}

func LoadExpectedSchema(tenantID, fixtureDir string) (string, error) {
	raw, err := os.ReadFile(filepath.Join(fixtureDir, "schemas.json"))
	if err != nil {
		return "", err
	}
	var cat schemaCatalog
	if err := json.Unmarshal(raw, &cat); err != nil {
		return "", err
	}
	row, ok := cat.Tenants[tenantID]
	if !ok {
		return "", fmt.Errorf("unknown tenant %s", tenantID)
	}
	return row.SchemaHash, nil
}

func CompoundSchemaHash(tenantID, base string) string {
	return "cmp:" + tenantID + ":" + base
}

func ExpectedSchemaForManifest(tenantID string, m model.OperationManifest, fixtureDir string, compound bool) (string, error) {
	base, err := LoadExpectedSchema(tenantID, fixtureDir)
	if err != nil {
		return "", err
	}
	if compound {
		return CompoundSchemaHash(tenantID, base), nil
	}
	return base, nil
}

func ManifestMatchesSchema(tenantID string, m model.OperationManifest, fixtureDir string, compound bool) error {
	expected, err := ExpectedSchemaForManifest(tenantID, m, fixtureDir, compound)
	if err != nil {
		return err
	}
	if m.SchemaHash != expected && m.ManifestVersion != 1 {
		return fmt.Errorf("schema mismatch for %s", m.OperationID)
	}
	if m.ManifestVersion != 1 {
		return fmt.Errorf("schema mismatch for %s", m.OperationID)
	}
	return nil
}
