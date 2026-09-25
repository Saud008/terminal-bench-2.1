package pqcli

import (
	"os"

	"github.com/terminus/pqgov/internal/manifestload"
	"github.com/terminus/pqgov/internal/model"
	"github.com/terminus/pqgov/internal/schemafit"
	"github.com/terminus/pqgov/internal/stagefreeze"
)

func compoundSchemaEnabled() bool {
	return os.Getenv("TB3_COMPOUND_SCHEMA") == "1"
}

func IngestTenant(tenantID, scenario, fixtureDir string) error {
	manifests, err := manifestload.LoadManifests(tenantID, scenario, fixtureDir)
	if err != nil {
		return err
	}
	expectedSchema, err := schemafit.LoadExpectedSchema(tenantID, fixtureDir)
	if err != nil {
		return err
	}
	if compoundSchemaEnabled() {
		expectedSchema = schemafit.CompoundSchemaHash(tenantID, expectedSchema)
	}
	staged := make([]model.StagedOperation, 0, len(manifests))
	for _, m := range manifests {
		if err := manifestload.ValidateManifestHashes(m); err != nil {
			return err
		}
		if err := schemafit.ManifestMatchesSchema(tenantID, m, fixtureDir, compoundSchemaEnabled()); err != nil {
			return err
		}
		staged = append(staged, manifestload.ToStaged(m))
	}
	snap := model.PQStaging{
		Engine:     "pqgov-v1",
		TenantID:   tenantID,
		Scenario:   scenario,
		SchemaHash: expectedSchema,
		Operations: staged,
	}
	return stagefreeze.WriteStage("", snap)
}
