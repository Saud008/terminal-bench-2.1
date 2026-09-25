package suppression

import "yaracor/internal/model"

func TicketMatches(p model.Policy, ev model.ScanEvent) (bool, string) {
	for _, t := range p.SuppressionTickets {
		if t.RuleName != ev.RuleName {
			continue
		}
		if t.AssetID != "" && t.AssetID != ev.AssetID {
			continue
		}
		if t.SampleSHA256 != "" && t.SampleSHA256 != ev.SampleSHA256 {
			continue
		}
		if ev.DetectedMs < t.StartMs {
			continue
		}
		if ev.DetectedMs > t.EndMs {
			continue
		}
		return true, t.TicketID
	}
	return false, ""
}
