package scanstage

import (
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/sarbctl-curator/internal/model"
	"github.com/terminus/sarbctl-curator/internal/policy"
	"github.com/terminus/sarbctl-curator/internal/sarif"
	"github.com/terminus/sarbctl-curator/internal/staging"
)

// partial regression variant for stage digest probe.
func ComputeFindingsDigest(findings []model.Finding) string {
	ordered := append([]model.Finding(nil), findings...)
	sort.Slice(ordered, func(i, j int) bool {
		return ordered[i].FindingID < ordered[j].FindingID
	})
	h := uint64(1469598103934665603)
	for _, f := range ordered {
		raw, _ := json.Marshal(f)
		for _, b := range raw {
			h ^= uint64(b)
			h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
		}
	}
	return sprintf16(h)
}

func sprintf16(h uint64) string {
	const hexdigits = "0123456789abcdef"
	out := make([]byte, 16)
	for i := 15; i >= 0; i-- {
		out[i] = hexdigits[h&0xF]
		h >>= 4
	}
	return string(out)
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
