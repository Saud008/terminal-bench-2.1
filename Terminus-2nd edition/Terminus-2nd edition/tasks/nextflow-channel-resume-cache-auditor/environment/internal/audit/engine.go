package audit

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/nfresume/internal/model"
	"github.com/terminus/nfresume/internal/staging"
)

const (
	findingsPath   = "/app/work/audit-findings.json"
	generationPath = "/app/state/audit-generation.json"
)

func Run(scenarioID string) error {
	var snap model.StageSnapshot
	if err := staging.ReadStage(staging.DefaultStagePath, &snap); err != nil {
		return err
	}
	if snap.Scenario != scenarioID {
		return fmt.Errorf("staging scenario mismatch")
	}

	findings := collectFindings(snap)
	if findings == nil {
		findings = []model.UnsafeFinding{}
	}
	sort.Slice(findings, func(i, j int) bool {
		if findings[i].TaskID == findings[j].TaskID {
			return findings[i].Rule < findings[j].Rule
		}
		return findings[i].TaskID < findings[j].TaskID
	})

	digest, err := auditDigest(findings)
	if err != nil {
		return err
	}
	doc := model.AuditFindings{
		Scenario:    scenarioID,
		UnsafeCount: len(findings),
		Findings:    findings,
		AuditDigest: digest,
	}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/work", 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(findingsPath, append(data, '\n'), 0o644); err != nil {
		return err
	}

	snap.AuditGen++
	if err := staging.WriteStage(staging.DefaultStagePath, snap); err != nil {
		return err
	}
	gen := model.GenerationFile{AuditGeneration: snap.AuditGen}
	gdata, _ := json.MarshalIndent(gen, "", "  ")
	return os.WriteFile(generationPath, append(gdata, '\n'), 0o644)
}

func collectFindings(snap model.StageSnapshot) []model.UnsafeFinding {
	var out []model.UnsafeFinding
	for _, t := range snap.Tasks {
		out = append(out, ruleFindings(snap, t)...)
		out = append(out, provenanceFindings(snap, t)...)
	}
	return out
}

func auditDigest(findings []model.UnsafeFinding) (string, error) {
	data, err := json.Marshal(findings)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}
