package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/fixdropcopy/internal/ledger"
	"github.com/terminus/fixdropcopy/internal/model"
	"github.com/terminus/fixdropcopy/internal/staging"
)

const generationPath = "/app/state/replay-generation.json"

func Run(scenarioID, outPath string) error {
	var snap model.StageSnapshot
	if err := staging.ReadStage(staging.DefaultStagePath, &snap); err != nil {
		return err
	}
	if snap.Scenario != scenarioID {
		return fmt.Errorf("scenario mismatch")
	}
	genData, err := os.ReadFile(generationPath)
	if err != nil {
		return err
	}
	var gen model.GenerationFile
	if err := json.Unmarshal(genData, &gen); err != nil {
		return err
	}
	if snap.ReplayGen == 0 || snap.ReplayGen != gen.ReplayGeneration {
		return fmt.Errorf("replay generation gate")
	}
	store, err := ledger.Open(ledger.DefaultDBPath)
	if err != nil {
		return err
	}
	defer store.Close()

	net, err := store.NetPositions()
	if err != nil {
		return err
	}
	active, err := store.ActiveRows()
	if err != nil {
		return err
	}
	bust, correct, cancel, err := store.CountByType()
	if err != nil {
		return err
	}
	var execIDs []string
	for _, r := range active {
		execIDs = append(execIDs, r.ExecID)
	}
	sort.Strings(execIDs)
	digest, err := auditDigest(net, execIDs)
	if err != nil {
		return err
	}
	doc := model.ComplianceExport{
		Scenario:         scenarioID,
		ReplayGeneration: snap.ReplayGen,
		NetPositions:     net,
		BustCount:        bust,
		CorrectionCount:  correct,
		CancelCount:      cancel,
		ActiveExecIDs:    execIDs,
		AuditDigest:      digest,
	}
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(outPath, data, 0o644)
}

func auditDigest(net map[string]int64, execIDs []string) (string, error) {
	payload := map[string]any{
		"net_positions":   net,
		"active_exec_ids": execIDs,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}
