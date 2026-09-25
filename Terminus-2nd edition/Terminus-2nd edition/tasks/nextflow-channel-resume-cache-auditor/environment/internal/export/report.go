package export

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/nfresume/internal/model"
	"github.com/terminus/nfresume/internal/staging"
)

const (
	findingsPath   = "/app/work/audit-findings.json"
	generationPath = "/app/state/audit-generation.json"
)

func Run(scenarioID, outPath string) error {
	var snap model.StageSnapshot
	if err := staging.ReadStage(staging.DefaultStagePath, &snap); err != nil {
		return err
	}
	if snap.Scenario != scenarioID {
		return fmt.Errorf("scenario mismatch")
	}

	findingsData, err := os.ReadFile(findingsPath)
	if err != nil {
		return err
	}
	var findings model.AuditFindings
	if err := json.Unmarshal(findingsData, &findings); err != nil {
		return err
	}
	if findings.Scenario != scenarioID {
		return fmt.Errorf("findings scenario mismatch")
	}

	doc := model.ExportReport{
		Scenario:        scenarioID,
		AuditGeneration: snap.AuditGen,
		UnsafeCount:     findings.UnsafeCount,
		Findings:        findings.Findings,
		AuditDigest:     findings.AuditDigest,
		SafeForResume:   findings.UnsafeCount == 0,
	}
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(outPath, append(data, '\n'), 0o644)
}
