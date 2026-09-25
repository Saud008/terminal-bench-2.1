package dedupe

import "yaracor/internal/model"

type key struct {
	asset string
	rule  string
	hash  string
}

func ClassifyDuplicates(events []model.ScanEvent) map[string]bool {
	bestMs := make(map[key]int64)
	bestID := make(map[key]string)
	dup := make(map[string]bool)
	for _, ev := range events {
		k := key{asset: ev.AssetID, rule: ev.RuleName, hash: ev.SampleSHA256}
		if prevMs, ok := bestMs[k]; !ok || ev.DetectedMs < prevMs || (ev.DetectedMs == prevMs && ev.EventID < bestID[k]) {
			if ok {
				dup[bestID[k]] = true
			}
			bestMs[k] = ev.DetectedMs
			bestID[k] = ev.EventID
			dup[ev.EventID] = false
		} else {
			dup[ev.EventID] = true
		}
	}
	return dup
}
