package riskbands

import (
	"strings"
	"time"

	"github.com/terminus/vaultaud/internal/model"
)

const scoreClamp = 200

// Score builds one tokens array entry from a staged row and the audit anchor.
func Score(row model.StagedLease, anchor time.Time) model.RiskToken {
	issued, _ := time.Parse(time.RFC3339, row.IssuedAt)
	elapsed := int(anchor.Sub(issued).Seconds())
	if elapsed < 0 {
		elapsed = 0
	}
	remaining := row.GrantedTTLSec - elapsed
	if remaining < 0 {
		remaining = 0
	}
	bucket, base := bucketFor(remaining)
	score := base
	if row.IsOrphan {
		score += 50
	}
	if !row.EffectiveRenewable {
		score += 25
	}
	if row.Admission == model.AdmissionDenied {
		score += 40
	}
	if strings.HasPrefix(row.LineageRoot, model.CyclePrefix) {
		score += 30
	}
	if score > scoreClamp {
		score = scoreClamp
	}
	expires := issued.UTC().Add(time.Duration(row.GrantedTTLSec) * time.Second)
	return model.RiskToken{
		TokenID:          row.TokenID,
		RenewalSeq:       row.RenewalSeq,
		LineageRoot:      row.LineageRoot,
		LineageDepth:     row.LineageDepth,
		IsOrphan:         row.IsOrphan,
		Admission:        row.Admission,
		RiskBucket:       bucket,
		RiskScore:        score,
		SecondsRemaining: remaining,
		ExpiresAt:        expires.Format(time.RFC3339),
	}
}

func bucketFor(sec int) (string, int) {
	if sec <= 300 {
		return "critical", 100
	}
	if sec <= 3600 {
		return "high", 70
	}
	if sec <= 86400 {
		return "medium", 40
	}
	return "low", 10
}
