package stagefreeze

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/pqgov/internal/model"
)

const DefaultStagePath = "/app/state/pq-staging.json"

func WriteStage(path string, snap model.PQStaging) error {
	if path == "" {
		path = DefaultStagePath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	digest, err := computeDigest(snap.TenantID, snap.Scenario, snap.SchemaHash, snap.Operations)
	if err != nil {
		return err
	}
	snap.StagingDigest = digest
	snap.OperationCount = len(snap.Operations)
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func ReadStage(path string) (model.PQStaging, error) {
	if path == "" {
		path = DefaultStagePath
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.PQStaging{}, err
	}
	var snap model.PQStaging
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.PQStaging{}, err
	}
	return snap, nil
}

func computeDigest(tenantID, scenario, schemaHash string, ops []model.StagedOperation) (string, error) {
	sorted := make([]model.StagedOperation, len(ops))
	copy(sorted, ops)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].OperationID < sorted[j].OperationID
	})
	payload := map[string]any{
		"tenant_id":   tenantID,
		"scenario":    scenario,
		"schema_hash": schemaHash,
		"operations":  sorted,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}

func CompactStageJSON(snap model.PQStaging) ([]byte, error) {
	type wire struct {
		Engine         string                  `json:"engine"`
		TenantID       string                  `json:"tenant_id"`
		Scenario       string                  `json:"scenario"`
		SchemaHash     string                  `json:"schema_hash"`
		OperationCount int                     `json:"operation_count"`
		Operations     []model.StagedOperation `json:"operations"`
		StagingDigest  string                  `json:"staging_digest"`
	}
	w := wire{
		Engine:         snap.Engine,
		TenantID:       snap.TenantID,
		Scenario:       snap.Scenario,
		SchemaHash:     snap.SchemaHash,
		OperationCount: snap.OperationCount,
		Operations:     snap.Operations,
		StagingDigest:  snap.StagingDigest,
	}
	return json.Marshal(w)
}
