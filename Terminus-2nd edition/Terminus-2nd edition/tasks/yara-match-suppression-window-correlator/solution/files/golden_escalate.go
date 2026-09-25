package criticality

import "yaracor/internal/model"

var tierOrder = []string{"low", "medium", "high", "critical"}

func EffectiveTier(p model.Policy, ev model.ScanEvent, defaultTier string) string {
	base := defaultTier
	for _, row := range p.AssetCriticality {
		if row.AssetID == ev.AssetID {
			base = row.Tier
			if ev.DetectedMs >= row.EscalationMs {
				return escalateOne(base)
			}
			return base
		}
	}
	return base
}

func escalateOne(tier string) string {
	for i, t := range tierOrder {
		if t == tier && i+1 < len(tierOrder) {
			return tierOrder[i+1]
		}
	}
	return tier
}
