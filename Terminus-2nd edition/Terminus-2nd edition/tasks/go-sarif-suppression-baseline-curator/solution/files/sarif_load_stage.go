package scanstage

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/sarbctl-curator/internal/model"
	"github.com/terminus/sarbctl-curator/internal/policy"
	"github.com/terminus/sarbctl-curator/internal/sarif"
	"github.com/terminus/sarbctl-curator/internal/staging"
)

type digestFinding struct {
	FindingID   string `json:"finding_id"`
	Tool        string `json:"tool"`
	RuleID      string `json:"rule_id"`
	Level       string `json:"level"`
	URI         string `json:"uri"`
	StartLine   int    `json:"start_line"`
	StartColumn int    `json:"start_column"`
	Fingerprint string `json:"fingerprint"`
	ObservedAt  string `json:"observed_at"`
}

func canonicalLine(f model.Finding) string {
	raw, _ := json.Marshal(digestFinding{
		FindingID: f.FindingID, Tool: f.Tool, RuleID: f.RuleID, Level: f.Level,
		URI: f.URI, StartLine: f.StartLine, StartColumn: f.StartColumn,
		Fingerprint: f.Fingerprint, ObservedAt: f.ObservedAt,
	})
	return string(raw)
}

func ComputeFindingsDigest(findings []model.Finding) string {
	ordered := append([]model.Finding(nil), findings...)
	sort.Slice(ordered, func(i, j int) bool {
		if ordered[i].ObservedAt == ordered[j].ObservedAt {
			return ordered[i].FindingID < ordered[j].FindingID
		}
		return ordered[i].ObservedAt < ordered[j].ObservedAt
	})
	body := ""
	for _, f := range ordered {
		body += canonicalLine(f) + "\n"
	}
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}

func WriteStaging(stagingPath, seqPath, sarifPath, policyPath, remapPath, baselinePath string, findings []model.Finding) error {
	sarifHash, err := sarif.SHA256File(sarifPath)
	if err != nil {
		return err
	}
	polHash, err := policy.SHA256File(policyPath)
	if err != nil {
		return err
	}
	rev, err := staging.BumpSeq(seqPath)
	if err != nil {
		return err
	}
	snap := model.FindingStaging{
		Findings:       findings,
		FindingsDigest: ComputeFindingsDigest(findings),
		SarifSHA256:    sarifHash,
		PolicySHA256:   polHash,
		PolicyPath:     policyPath,
		RemapPath:      remapPath,
		BaselinePath:   baselinePath,
		ScanRevision:   rev,
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(stagingPath, raw, 0o644)
}
