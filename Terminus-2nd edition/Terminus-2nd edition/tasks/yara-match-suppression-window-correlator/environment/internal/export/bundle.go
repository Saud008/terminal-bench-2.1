package export

import (
	"encoding/json"
	"fmt"
	"os"

	"yaracor/internal/correlate"
	"yaracor/internal/model"
)

func BuildBundle(gen model.CorrelateGeneration) model.IncidentBundle {
	return model.IncidentBundle{
		CorrelateGeneration: gen.Generation,
		StagingGeneration:   gen.StagingGeneration,
		Incidents:           gen.Incidents,
		BundleDigest:        "pending",
	}
}

func WriteBundle(path string, bundle model.IncidentBundle) error {
	raw, err := json.MarshalIndent(bundle, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

func RunExport(snap model.EventStaging, genPath, outPath string) error {
	gen, err := correlate.ReadGeneration(genPath)
	if err != nil {
		return err
	}
	if gen.Generation < 1 {
		return fmt.Errorf("correlate_generation zero")
	}
	bundle := BuildBundle(gen)
	return WriteBundle(outPath, bundle)
}
