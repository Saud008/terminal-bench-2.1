package export

import (
	"encoding/json"
	"os"

	"github.com/terminus/modbus-drift-cataloger/internal/catalog"
	"github.com/terminus/modbus-drift-cataloger/internal/model"
)

// Broken export-only: skips frames_digest validation and catalog_generation gate.
func BuildDriftCatalog(gen model.CatalogGeneration) model.DriftCatalog {
	return model.DriftCatalog{
		CatalogGeneration: gen.Generation,
		StagingGeneration: gen.StagingGeneration,
		Entries:           gen.Entries,
		CatalogDigest:     "pending",
	}
}

func WriteDriftCatalog(path string, cat model.DriftCatalog) error {
	raw, err := json.MarshalIndent(cat, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

func RunExport(snap model.PollStaging, genPath, outPath string) error {
	gen, err := catalog.ReadGeneration(genPath)
	if err != nil {
		return err
	}
	drift := BuildDriftCatalog(gen)
	return WriteDriftCatalog(outPath, drift)
}
