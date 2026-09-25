package quarantine

import "yaracor/internal/model"

func IsQuarantined(p model.Policy, ev model.ScanEvent) bool {
	for _, q := range p.QuarantineStates {
		if q.AssetID != ev.AssetID || q.SampleSHA256 != ev.SampleSHA256 {
			continue
		}
		if q.State != "active" && q.State != "released" {
			continue
		}
		if ev.DetectedMs < q.EnteredMs {
			continue
		}
		return true
	}
	return false
}
