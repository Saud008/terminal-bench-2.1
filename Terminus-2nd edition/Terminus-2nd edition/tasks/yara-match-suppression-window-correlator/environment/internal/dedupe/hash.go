package dedupe

import "yaracor/internal/model"

type key struct {
	asset string
	rule  string
	hash  string
}

func ClassifyDuplicates(events []model.ScanEvent) map[string]bool {
	bestMs := make(map[key]int64)
	dup := make(map[string]bool)
	for _, ev := range events {
		k := key{asset: ev.AssetID, rule: ev.RuleName, hash: ev.SampleSHA256}
		if prev, ok := bestMs[k]; !ok || ev.DetectedMs > prev {
			if ok {
				dup[ev.EventID] = false
			}
			bestMs[k] = ev.DetectedMs
		} else {
			dup[ev.EventID] = true
		}
	}
	return dup
}
