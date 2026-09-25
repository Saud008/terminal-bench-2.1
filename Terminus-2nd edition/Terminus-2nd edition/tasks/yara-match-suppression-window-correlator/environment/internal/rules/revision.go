package rules

import "yaracor/internal/model"

func RevisionActive(p model.Policy, ev model.ScanEvent) bool {
	for _, rev := range p.RuleRevisions {
		if rev.RuleName != ev.RuleName || rev.RevisionID != ev.RuleRevision {
			continue
		}
		if ev.DetectedMs < rev.EffectiveMs {
			return false
		}
		if ev.DetectedMs >= rev.RetiredMs {
			return false
		}
		return true
	}
	return false
}
