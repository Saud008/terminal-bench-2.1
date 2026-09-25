package catalog

import (
	"encoding/json"
	"os"

	"github.com/terminus/modbus-drift-cataloger/internal/model"
)

func ReadGeneration(path string) (model.CatalogGeneration, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.CatalogGeneration{}, err
	}
	var gen model.CatalogGeneration
	if err := json.Unmarshal(raw, &gen); err != nil {
		return model.CatalogGeneration{}, err
	}
	return gen, nil
}

func WriteGeneration(path string, gen model.CatalogGeneration) error {
	raw, err := json.MarshalIndent(gen, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}
